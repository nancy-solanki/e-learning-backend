from apps.common.models import Files


class FileRepository:
    """
    Repository to handle database interactions relating to the Files model.
    """

    @staticmethod
    def get_file_by_id(file_id):
        return Files.objects.filter(id=file_id).first()

    @staticmethod
    def get_all_files():
        """Returns a queryset of all files."""
        return Files.objects.all()

    @staticmethod
    def create_file(url, name, file_type, size):
        return Files.objects.create(url=url, name=name, type=file_type, size=size)

    @staticmethod
    def delete_file(file_id):
        file = Files.objects.filter(id=file_id).first()
        if file:
            file.delete()
            return True
        return False
