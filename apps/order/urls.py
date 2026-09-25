from django.urls import path

from .views import (
    MakePayment,
    OrderInstructorView,
    OrderView,
    SingleOrderInstructorView,
    SingleOrderView,
    SuccessPayment,
)

app_name = "order"

urlpatterns = [
    path("user/", OrderView.as_view(), name="order-list"),
    path("user/<uuid:pk>/", SingleOrderView.as_view(), name="order-detail"),
    path("instructor/", OrderInstructorView.as_view(), name="order-instructor-list"),
    path(
        "instructor/<uuid:pk>/",
        SingleOrderInstructorView.as_view(),
        name="order-instructor-detail",
    ),
    path("make-payment/", MakePayment.as_view(), name="make-payment"),
    path("success-payment/", SuccessPayment.as_view(), name="success-payment"),
]
