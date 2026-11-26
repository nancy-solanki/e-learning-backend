import re

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permission import IsInstructorOrAdmin

from . import uploads


class InitiateUploadSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(
        max_length=255, default="application/octet-stream"
    )
    kind = serializers.ChoiceField(choices=("video", "resource"), default="video")
    size = serializers.IntegerField(min_value=1)

    def validate_size(self, value):
        data = getattr(self, "initial_data", {})
        limit = (
            settings.MAX_LECTURE_RESOURCE_SIZE
            if data.get("kind") == "resource"
            else settings.MAX_LECTURE_VIDEO_SIZE
        )
        if value > limit:
            raise serializers.ValidationError("File exceeds the configured size limit.")
        return value

    def validate(self, attrs):
        if attrs["kind"] == "video" and not attrs["content_type"].startswith("video/"):
            raise serializers.ValidationError(
                {"content_type": "Video uploads need a video content type."}
            )
        return attrs


class UploadPartSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=1024)
    upload_id = serializers.CharField(max_length=2048)
    part_number = serializers.IntegerField(min_value=1, max_value=10000)


class AbortUploadSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=1024)
    upload_id = serializers.CharField(max_length=2048)


class CompleteUploadSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=1024)
    upload_id = serializers.CharField(max_length=2048)
    parts = serializers.ListField(child=serializers.DictField(), min_length=1)

    def validate_parts(self, parts):
        for part in parts:
            if set(part) != {"ETag", "PartNumber"}:
                raise serializers.ValidationError(
                    "Each part needs ETag and PartNumber."
                )
            if (
                not isinstance(part["PartNumber"], int)
                or not 1 <= part["PartNumber"] <= 10000
            ):
                raise serializers.ValidationError("Invalid part number.")
            if not isinstance(part["ETag"], str) or not re.fullmatch(
                r'"?[a-fA-F0-9-]+"?', part["ETag"]
            ):
                raise serializers.ValidationError("Invalid part ETag.")
        if [p["PartNumber"] for p in parts] != sorted({p["PartNumber"] for p in parts}):
            raise serializers.ValidationError(
                "Parts must be unique and ordered by part number."
            )
        return parts


class ResourceDownloadSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=1024)


class MultipartUploadView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @extend_schema(request=InitiateUploadSerializer, responses={201: dict})
    def post(self, request):
        serializer = InitiateUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = uploads.initiate_upload(
            request.user.pk,
            serializer.validated_data["filename"],
            serializer.validated_data["content_type"],
            serializer.validated_data["kind"],
        )
        return Response(
            {
                **upload,
                "part_size": settings.S3_MULTIPART_PART_SIZE,
                "max_size": (
                    settings.MAX_LECTURE_RESOURCE_SIZE
                    if serializer.validated_data["kind"] == "resource"
                    else settings.MAX_LECTURE_VIDEO_SIZE
                ),
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=UploadPartSerializer, responses={200: dict})
    def put(self, request):
        serializer = UploadPartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            url = uploads.sign_upload_part(
                request.user.pk, data["key"], data["upload_id"], data["part_number"]
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response({"url": url})

    @extend_schema(request=CompleteUploadSerializer, responses={200: dict})
    def patch(self, request):
        serializer = CompleteUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            etag = uploads.complete_upload(
                request.user.pk, data["key"], data["upload_id"], data["parts"]
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response({"key": data["key"], "etag": etag})

    @extend_schema(request=UploadPartSerializer, responses={204: None})
    def delete(self, request):
        serializer = AbortUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            uploads.abort_upload(request.user.pk, data["key"], data["upload_id"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResourceDownloadUrlView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[ResourceDownloadSerializer], responses={200: dict})
    def get(self, request):
        serializer = ResourceDownloadSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            url = uploads.create_download_url(serializer.validated_data["key"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"url": url, "expires_in": settings.S3_PRESIGNED_URL_TTL})
