from datetime import datetime, timedelta

from moviepy import VideoFileClip

from .repository import LectureRepository


class LectureService:
    """
    Service to handle business logic relating to the Lecture model.
    """

    @staticmethod
    def create_lecture(user, validated_data) -> str:
        """
        Handles the creation of a lecture, including video duration calculation
        and updating course/section status if published.
        """
        source = validated_data.get("source")
        mins, secs = 0, 0
        duration_str = None

        if source and hasattr(source, "temporary_file_path"):
            try:
                clip = VideoFileClip(source.temporary_file_path())
                video_duration = int(clip.duration)
                mins, secs = divmod(video_duration, 60)
                duration_str = f"{str(mins).zfill(2)}:{str(secs).zfill(2)}"
            except Exception:
                # Fallback if video processing fails
                pass

        # Call repository to create lecture
        lecture = LectureRepository.create_lecture(
            user=user, duration=duration_str, **validated_data
        )

        # Handle publication logic if status is published
        if validated_data.get("status") == "published":
            LectureService._handle_publication(lecture, mins)

        return "Lecture created successfully"

    @staticmethod
    def _handle_publication(lecture, mins):
        """
        Updates course total hours and section status when a lecture is published.
        """
        course = lecture.course
        section = lecture.section

        # Update course total hours
        try:
            current_hours = course.total_hours
            # Handle both HH:MM and HH:MM:SS formats if possible
            if len(current_hours.split(":")) == 2:
                time_format = "%H:%M"
            else:
                time_format = "%H:%M:%S"

            current_time = datetime.strptime(current_hours, time_format)
            new_time = (current_time + timedelta(minutes=mins)).time()
            course.total_hours = new_time.strftime("%H:%M:%S")
            course.save()
        except Exception:
            pass

        # Update section status
        section.status = "published"
        section.save()

    @staticmethod
    def toggle_lecture_status(lecture) -> str:
        """
        Toggles the deleted status (soft delete/restore) of a lecture.
        """
        action = lecture.toggle_deleted()
        return f"Lecture {action} successfully"
