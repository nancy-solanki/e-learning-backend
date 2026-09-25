from .models import Order


class OrderRepository:
    """
    Repository to handle database interactions for Order.
    """

    @staticmethod
    def get_order_queryset():
        return Order.objects.filter(deleted_at__isnull=True)

    @staticmethod
    def get_user_orders(user):
        return OrderRepository.get_order_queryset().filter(user=user)

    @staticmethod
    def get_instructor_orders(user):
        return OrderRepository.get_order_queryset().filter(instructor=user)

    @staticmethod
    def get_order_by_id(order_id):
        return OrderRepository.get_order_queryset().filter(id=order_id).first()

    @staticmethod
    def create_order(**kwargs):
        return Order.objects.create(**kwargs)

    @staticmethod
    def update_order(order, **kwargs):
        for field, value in kwargs.items():
            setattr(order, field, value)
        order.save()
        return order

    @staticmethod
    def soft_delete_order(order):
        return order.soft_delete()

    @staticmethod
    def restore_order(order):
        return order.restore()

    @staticmethod
    def toggle_order_status(order):
        return order.toggle_deleted()
