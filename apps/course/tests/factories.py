import factory

from apps.common.tests.factories import FileFactory
from apps.course.models import Course
from apps.users.tests.factories import UserFactory


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    title = factory.Sequence(lambda n: f"Course {n}")
    slug = factory.Sequence(lambda n: f"course-{n}")
    instructor = factory.SubFactory(UserFactory)
    thumbnail = factory.SubFactory(FileFactory)
    short_description = "Learn Python"
    long_description = "A Python course"
    learn_description_points = "Basics"
    requirements = "None"
