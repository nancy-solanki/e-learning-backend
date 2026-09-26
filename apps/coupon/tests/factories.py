import factory

from apps.coupon.models import Coupon
from apps.course.tests.factories import CourseFactory


class CouponFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Coupon

    course = factory.SubFactory(CourseFactory)
    code = factory.Sequence(lambda n: f"SAVE{n}")
