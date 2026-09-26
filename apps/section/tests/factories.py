import factory

from apps.course.tests.factories import CourseFactory
from apps.section.models import Section


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Section

    title = factory.Sequence(lambda n: f"Section {n}")
    slug = factory.Sequence(lambda n: f"section-{n}")
    description = "Introduction"
    course = factory.SubFactory(CourseFactory)
    instructor = factory.SelfAttribute("course.instructor")
