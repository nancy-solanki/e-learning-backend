import json
import math
import os

import razorpay

from apps.coupon.models import Coupon
from apps.course.models import Course
from apps.enroll.repository import EnrollRepository
from apps.wallet.models import Wallet
from apps.wallet.repository import WalletRepository

from .repository import OrderRepository


class OrderService:
    """
    Service to handle business logic for Order.
    """

    @staticmethod
    def get_order_queryset():
        return OrderRepository.get_order_queryset()

    @staticmethod
    def get_user_orders(user):
        return OrderRepository.get_user_orders(user)

    @staticmethod
    def get_instructor_orders(user):
        return OrderRepository.get_instructor_orders(user)

    @staticmethod
    def create_razorpay_order(total_paid, course_id, user):
        """
        Creates a Razorpay order for payment.
        """
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ValueError("Course not found")

        if course.instructor == user:
            raise ValueError("You can't enroll in your own course!")

        enroll = (
            EnrollRepository.get_enrollments_by_course(course).filter(user=user).first()
        )
        if enroll:
            raise ValueError("Already enrolled in this course!")

        razorpay_client = razorpay.Client(
            auth=(os.environ.get("RAZOR_KEY_ID"), os.environ.get("RAZOR_KEY_SECRET"))
        )

        payment = razorpay_client.order.create(
            {"amount": int(total_paid) * 100, "currency": "INR", "payment_capture": "1"}
        )
        return payment

    @staticmethod
    def process_successful_payment(data, user):
        """
        Processes successful payment and updates related records.
        """
        total = math.floor(float(data["total_paid"]))
        course_id = data["course"]
        coupon_id = data.get("coupon")
        is_free = data.get("is_free", False)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return False, "Course not found"

        coupon = None
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
            except Coupon.DoesNotExist:
                pass

        if coupon:
            if not coupon.is_unlimited:
                coupon.used = coupon.used + 1
                coupon.save()

        order = OrderRepository.create_order(
            course=course,
            user=user,
            instructor=course.instructor,
            total_paid=total,
            coupon=coupon,
        )

        enroll = EnrollRepository.create_enrollment(user=user, course=course)
        order.enroll = enroll
        order.save()

        if not is_free:
            try:
                res = (
                    json.loads(data["response"])
                    if isinstance(data["response"], str)
                    else data["response"]
                )
                verification_data = {
                    "razorpay_order_id": res.get("razorpay_order_id"),
                    "razorpay_payment_id": res.get("razorpay_payment_id"),
                    "razorpay_signature": res.get("razorpay_signature"),
                }

                razorpay_client = razorpay.Client(
                    auth=(
                        os.environ.get("RAZOR_KEY_ID"),
                        os.environ.get("RAZOR_KEY_SECRET"),
                    )
                )

                check = razorpay_client.utility.verify_payment_signature(
                    verification_data
                )

                if check is None:
                    order.status = "rejected"
                    order.save()
                    return False, "Payment verification failed"
            except (json.JSONDecodeError, KeyError, Exception) as e:
                order.status = "rejected"
                order.save()
                return False, f"Error processing payment response: {str(e)}"

        admin_fee = math.floor(total * (10 / 100))
        instructor_earning = total - admin_fee

        order.admin_commission = admin_fee
        order.status = "success"
        order.save()

        # Update Wallets
        site_wallet = WalletRepository.get_site_wallet()
        admin_wallets = Wallet.objects.filter(
            user__is_admin=True, deleted_at__isnull=True
        )
        instructor_wallet = WalletRepository.get_wallet_by_user(course.instructor)

        if site_wallet:
            site_wallet.current_earnings += total
            site_wallet.total_earnings += total
            site_wallet.save()

        if instructor_wallet:
            instructor_wallet.current_earnings += instructor_earning
            instructor_wallet.total_earnings += instructor_earning
            instructor_wallet.save()

        if admin_wallets.exists():
            count = admin_wallets.count()
            single_admin_earning = admin_fee / count
            for wallet in admin_wallets:
                wallet.current_earnings += single_admin_earning
                wallet.total_earnings += single_admin_earning
                wallet.save()

        return True, "Payment success"
