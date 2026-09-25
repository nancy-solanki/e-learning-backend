from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CouponViewSet, GetCoupon

app_name = "coupon"

router = DefaultRouter()
router.register(r'management', CouponViewSet, basename='coupon-management')

urlpatterns = [
    path('', include(router.urls)),
    path('validate/<code>/', GetCoupon.as_view(), name='get-coupon'),
]
