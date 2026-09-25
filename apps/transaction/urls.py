from django.urls import path

from .views import SingleTransactionView, TransactionView

app_name = "transaction"

urlpatterns = [
    path("", TransactionView.as_view(), name="transaction_list"),
    path("<uuid:pk>/", SingleTransactionView.as_view(), name="transaction_detail"),
]
