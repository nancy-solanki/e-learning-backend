from django.urls import path

from .views import (
    MakePayment,
    OrderView,
    SingleOrderView,
    SuccessPayment,
)

app_name = "order"

urlpatterns = [
    path("user/", OrderView.as_view(), name="order-list"),
    path("user/<uuid:pk>/", SingleOrderView.as_view(), name="order-detail"),
    path("make-payment/", MakePayment.as_view(), name="make-payment"),
    path("success-payment/", SuccessPayment.as_view(), name="success-payment"),
]
