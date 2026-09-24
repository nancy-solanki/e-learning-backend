from .repository import SectionRepository


class SectionService:
    """
    Service to handle business logic for Section.
    """

    @staticmethod
    def get_public_queryset():
        return SectionRepository.get_all_published_sections()

    @staticmethod
    def get_queryset_for_user(user):
        return SectionRepository.get_user_sections(user)

    @staticmethod
    def get_sections_by_course(course):
        return SectionRepository.get_sections_by_course(course)

    @staticmethod
    def toggle_section_status(section):
        """
        Toggles the soft delete status of a section.
        """
        return SectionRepository.toggle_section_status(section)

    @staticmethod
    def delete_section(section):
        """
        Soft deletes a section.
        """
        return SectionRepository.soft_delete_section(section)

    @staticmethod
    def restore_section(section):
        """
        Restores a soft-deleted section.
        """
        return SectionRepository.restore_section(section)
