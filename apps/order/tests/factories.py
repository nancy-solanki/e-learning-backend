import factory

from apps.course.tests.factories import CourseFactory
from apps.order.models import Order
from apps.users.tests.factories import UserFactory


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    instructor = factory.SelfAttribute("course.instructor")
    total_paid = 100
