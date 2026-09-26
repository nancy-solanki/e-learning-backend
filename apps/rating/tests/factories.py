from decimal import Decimal

import factory

from apps.course.tests.factories import CourseFactory
from apps.rating.models import Rating
from apps.users.tests.factories import UserFactory


class RatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rating

    course = factory.SubFactory(CourseFactory)
    user = factory.SubFactory(UserFactory)
    rating = Decimal("4.0")
    comment = "Helpful course"
