import os
import uuid

from django.conf import settings


def s3_client():
    import boto3

    return boto3.client("s3", region_name=settings.AWS_REGION)


def initiate_upload(user_id, filename, content_type, kind="video"):
    safe_name = os.path.basename(filename).replace(" ", "_")
    upload_token = uuid.uuid4()
    prefix = "resources" if kind == "resource" else "source"
    key = f"{prefix}/{user_id}/{upload_token}/{safe_name}"
    result = s3_client().create_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        ContentType=content_type,
        Metadata={"upload-token": str(upload_token)},
    )
    return {"key": key, "upload_id": result["UploadId"]}


def sign_upload_part(user_id, key, upload_id, part_number):
    _validate_key_owner(user_id, key)
    return s3_client().generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": key,
            "UploadId": upload_id,
            "PartNumber": part_number,
        },
        ExpiresIn=settings.S3_PRESIGNED_URL_TTL,
    )


def complete_upload(user_id, key, upload_id, parts):
    _validate_key_owner(user_id, key)
    client = s3_client()
    listed_parts = []
    marker = 0
    while True:
        page = client.list_parts(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            UploadId=upload_id,
            PartNumberMarker=marker,
        )
        listed_parts.extend(page.get("Parts", []))
        if not page.get("IsTruncated"):
            break
        marker = page["NextPartNumberMarker"]
    max_size = (
        settings.MAX_LECTURE_RESOURCE_SIZE
        if key.startswith("resources/")
        else settings.MAX_LECTURE_VIDEO_SIZE
    )
    if sum(part["Size"] for part in listed_parts) > max_size:
        client.abort_multipart_upload(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key, UploadId=upload_id
        )
        raise ValueError("File exceeds the configured size limit.")
    result = client.complete_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )
    return result.get("ETag")


def abort_upload(user_id, key, upload_id):
    _validate_key_owner(user_id, key)
    s3_client().abort_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key, UploadId=upload_id
    )


def create_download_url(key):
    if not key.startswith("resources/"):
        raise ValueError("Invalid resource key.")
    return s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=settings.S3_PRESIGNED_URL_TTL,
    )


def _validate_key_owner(user_id, key):
    if not any(
        key.startswith(f"{prefix}/{user_id}/") for prefix in ("source", "resources")
    ):
        raise ValueError("Upload does not belong to the authenticated user.")
