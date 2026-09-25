from .models import Coupon


class CouponRepository:
    """
    Repository to handle database interactions relating to the Coupon model.
    """

    @staticmethod
    def get_all_coupons():
        """Returns a queryset of all coupons for admin."""
        return Coupon.objects.all().order_by("-created_at")

    @staticmethod
    def get_instructor_coupons(user):
        """Returns a queryset of coupons created by/for the instructor."""
        return Coupon.objects.filter(
            deleted_at__isnull=True,
            is_instructor_created=True,
            course__instructor=user
        ).order_by("-created_at")

    @staticmethod
    def get_active_coupons():
        """Returns a queryset of active (not deleted) coupons."""
        return Coupon.objects.filter(deleted_at__isnull=True).order_by("-created_at")

    @staticmethod
    def get_coupon_by_code(code):
        """Returns a single coupon by its unique code."""
        return Coupon.objects.filter(code=code, deleted_at__isnull=True).first()

    @staticmethod
    def create_coupon(**validated_data):
        """Creates a new coupon."""
        return Coupon.objects.create(**validated_data)

    @staticmethod
    def save(coupon):
        """Saves a coupon instance."""
        coupon.save()
        return coupon
