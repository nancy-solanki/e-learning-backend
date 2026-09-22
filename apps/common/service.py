import cloudinary.uploader

from apps.common.repository import FileRepository

ALLOWED_FILE_TYPES = ['image/', 'video/', 'application/pdf']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB in bytes


class FileService:
    """
    Service to handle business logic relating to the Files model.
    """

    @staticmethod
    def upload_file_to_cloud(file, folder):
        if not any(file.content_type.startswith(file_type) for file_type in ALLOWED_FILE_TYPES):
            raise ValueError(f"File type '{file.content_type}' is not allowed. Only image, video files and PDFs are allowed.")

        if file.size > MAX_FILE_SIZE:
            raise ValueError(f"File '{file.name}' is too large. Maximum file size is 5 MB.")

        try:
            response = cloudinary.uploader.upload(file=file, folder=folder)
        except Exception as e:
            raise ValueError(f"{str(e)}")
        return FileRepository.create_file(
            url=response['secure_url'],
            name=file.name,
            file_type=file.content_type,
            size=file.size
        )
