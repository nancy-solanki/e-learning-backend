from datetime import date

from .repository import CouponRepository


class CouponService:
    """
    Service to handle business logic relating to the Coupon model.
    """

    @staticmethod
    def get_coupons(user):
        """Returns coupons based on user role."""
        if user.is_admin:
            return CouponRepository.get_all_coupons()
        return CouponRepository.get_instructor_coupons(user)

    @staticmethod
    def toggle_coupon_status(coupon) -> str:
        """Toggles the deleted status (soft delete/restore) of a coupon."""
        action = coupon.toggle_deleted()
        return f"Coupon {action} successfully"

    @staticmethod
    def validate_coupon(code):
        """Validates a coupon by code, checking limit and expiration."""
        coupon = CouponRepository.get_coupon_by_code(code)
        if not coupon:
            return None, "Coupon not found!"

        if not coupon.is_unlimited:
            if coupon.used >= coupon.limit:
                return None, "Coupon usage limit reached!"

        if coupon.expired_at and coupon.expired_at < date.today():
            return None, "Coupon has expired!"

        return coupon, None
