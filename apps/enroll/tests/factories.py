import factory

from apps.course.tests.factories import CourseFactory
from apps.enroll.models import Enroll
from apps.users.tests.factories import UserFactory


class EnrollFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enroll

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
