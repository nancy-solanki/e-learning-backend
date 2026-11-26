import os
import uuid

import boto3
from django.conf import settings

from apps.common.repository import FileRepository

ALLOWED_FILE_TYPES = ["image/", "video/", "application/pdf"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB in bytes


class FileService:
    """
    Service to handle business logic relating to the Files model.
    """

    @staticmethod
    def upload_file_to_s3(file, folder):
        if not any(
            file.content_type.startswith(file_type) for file_type in ALLOWED_FILE_TYPES
        ):
            raise ValueError(
                f"File type '{file.content_type}' is not allowed. "
                "Only image, video files and PDFs are allowed."
            )

        if file.size > MAX_FILE_SIZE:
            raise ValueError(
                f"File '{file.name}' is too large. Maximum file size is 5 MB."
            )

        try:
            if not settings.AWS_STORAGE_BUCKET_NAME:
                raise ValueError("AWS_STORAGE_BUCKET_NAME is not configured.")
            if not settings.CLOUDFRONT_DOMAIN:
                raise ValueError("CLOUDFRONT_DOMAIN is not configured.")
            key = f"{folder}/{uuid.uuid4().hex}{os.path.splitext(file.name)[1]}"
            boto3.client("s3", region_name=settings.AWS_REGION).put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=key,
                Body=file,
                ContentType=file.content_type,
            )
            url = f"{settings.CLOUDFRONT_DOMAIN}/{key}"
        except Exception as e:
            raise ValueError(f"{str(e)}")
        return FileRepository.create_file(
            url=url,
            name=file.name,
            file_type=file.content_type,
            size=file.size,
        )
