import factory

from apps.lecture.models import Lecture
from apps.section.tests.factories import SectionFactory


class LectureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lecture

    title = factory.Sequence(lambda n: f"Lecture {n}")
    slug = factory.Sequence(lambda n: f"lecture-{n}")
    description = "Introduction"
    lecture_type = "document"
    document_content = "Lesson content"
    section = factory.SubFactory(SectionFactory)
    course = factory.SelfAttribute("section.course")
    instructor = factory.SelfAttribute("course.instructor")
