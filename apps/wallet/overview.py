import csv
from datetime import datetime, time, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bank.repository import BankRepository

from .models import Wallet, WalletEntry
from .permissions import IsWalletUser


class WalletQuery(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    search = serializers.CharField(required=False, max_length=255)
    type = serializers.ChoiceField(choices=WalletEntry.Kind.choices, required=False)
    status = serializers.ChoiceField(choices=WalletEntry.Status.choices, required=False)
    page = serializers.IntegerField(min_value=1, required=False)

    def validate(self, data):
        today = timezone.now().date()
        data.setdefault("end", today)
        data.setdefault("start", data["end"].replace(day=1))
        if data["start"] > data["end"]:
            raise serializers.ValidationError("start must be on or before end")
        if data["end"] >= datetime.max.date():
            raise serializers.ValidationError("end is out of range")
        return data


class EntrySerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source="created_at")

    class Meta:
        model = WalletEntry
        fields = (
            "id",
            "reference",
            "description",
            "date",
            "completed_at",
            "type",
            "status",
            "amount",
            "account_last4",
        )


class SummarySerializer(serializers.Serializer):
    available_balance = serializers.DecimalField(max_digits=18, decimal_places=2)
    period_earnings = serializers.DecimalField(max_digits=18, decimal_places=2)
    completed_payouts = serializers.DecimalField(max_digits=18, decimal_places=2)
    refunds = serializers.DecimalField(max_digits=18, decimal_places=2)
    pending_payout_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    pending_payout_count = serializers.IntegerField()
    earning_count = serializers.IntegerField()
    completed_payout_count = serializers.IntegerField()
    refund_count = serializers.IntegerField()
    latest_pending_payout_at = serializers.DateTimeField(allow_null=True)


class AccountSerializer(serializers.Serializer):
    type = serializers.CharField()
    bank_name = serializers.CharField()
    account_last4 = serializers.CharField()


class PeriodSerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()
    timezone = serializers.CharField()


class OverviewSerializer(serializers.Serializer):
    currency = serializers.CharField()
    as_of = serializers.DateTimeField()
    opening_balance = serializers.DecimalField(
        max_digits=18, decimal_places=2, allow_null=True
    )
    history_started_at = serializers.DateTimeField()
    history_complete = serializers.BooleanField()
    period = PeriodSerializer()
    summary = SummarySerializer()
    payout_account = AccountSerializer(allow_null=True)


def total(queryset):
    return queryset.aggregate(value=Sum("amount"))["value"] or Decimal(0)


class WalletReadView(APIView):
    permission_classes = [IsWalletUser]

    def wallet(self):
        return get_object_or_404(
            Wallet.objects.filter(
                user=self.request.user, deleted_at__isnull=True, is_site_wallet=False
            ).order_by("pk")
        )

    def selection(self, wallet):
        query = WalletQuery(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        start = datetime.combine(data["start"], time.min, dt_timezone.utc)
        end = datetime.combine(
            data["end"] + timedelta(days=1), time.min, dt_timezone.utc
        )
        return data, start, end

    def entries(self, wallet):
        data, start, end = self.selection(wallet)
        entries = wallet.entries.filter(created_at__gte=start, created_at__lt=end)
        for field in ("type", "status"):
            if field in data:
                entries = entries.filter(**{field: data[field]})
        if data.get("search"):
            entries = entries.filter(
                Q(description__icontains=data["search"])
                | Q(reference__icontains=data["search"])
            )
        return entries


class WalletOverviewView(WalletReadView):
    @extend_schema(
        tags=["Wallet"], parameters=[WalletQuery], responses=OverviewSerializer
    )
    def get(self, request):
        wallet = self.wallet()
        data, start, end = self.selection(wallet)
        completed = wallet.entries.filter(status="completed")
        period = completed.filter(completed_at__gte=start, completed_at__lt=end)
        earnings = period.filter(type="earning")
        payouts = period.filter(type="withdrawal")
        refunds = period.filter(type="refund")
        pending = wallet.entries.filter(type="withdrawal", status="pending")
        reserved = -total(pending)
        latest = pending.first()
        bank = BankRepository.get_default_bank(request.user)
        complete = start >= wallet.history_started_at
        result = {
            "currency": wallet.currency,
            "as_of": timezone.now(),
            "history_started_at": wallet.history_started_at,
            "history_complete": complete,
            "opening_balance": (
                total(completed.filter(completed_at__lt=start)) if complete else None
            ),
            "period": {"start": data["start"], "end": data["end"], "timezone": "UTC"},
            "summary": {
                "available_balance": wallet.current_earnings - reserved,
                "period_earnings": total(earnings),
                "completed_payouts": -total(payouts),
                "refunds": -total(refunds),
                "pending_payout_amount": reserved,
                "pending_payout_count": pending.count(),
                "earning_count": earnings.count(),
                "completed_payout_count": payouts.count(),
                "refund_count": refunds.count(),
                "latest_pending_payout_at": latest.created_at if latest else None,
            },
            "payout_account": (
                {
                    "type": "bank_transfer",
                    "bank_name": bank.name,
                    "account_last4": bank.account_number[-4:],
                }
                if bank
                else None
            ),
        }
        return Response(OverviewSerializer(result).data)


class EntryPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EntrySerializer(many=True)


class WalletEntriesView(WalletReadView):
    @extend_schema(
        operation_id="wallet_transactions_list",
        tags=["Wallet"],
        parameters=[WalletQuery],
        responses=EntryPageSerializer,
    )
    def get(self, request):
        entries = self.entries(self.wallet())
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(entries, request)
        return paginator.get_paginated_response(EntrySerializer(page, many=True).data)


class WalletEntryView(WalletReadView):
    @extend_schema(tags=["Wallet"], responses=EntrySerializer)
    def get(self, request, pk):
        entry = get_object_or_404(self.wallet().entries, pk=pk)
        return Response(EntrySerializer(entry).data)


class WalletExportView(WalletReadView):
    @extend_schema(
        tags=["Wallet"], parameters=[WalletQuery], responses={(200, "text/csv"): str}
    )
    def get(self, request):
        wallet = self.wallet()
        entries = self.entries(wallet)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="wallet-transactions.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "Reference",
                "Description",
                "Date (UTC)",
                "Type",
                "Status",
                "Amount",
                "Currency",
            ]
        )
        for entry in entries.iterator():
            row = [
                entry.reference,
                entry.description,
                entry.created_at.isoformat(),
                entry.type,
                entry.status,
                str(entry.amount),
                wallet.currency,
            ]
            # Prevent spreadsheet formulas in user-controlled text, preserving numeric amounts.
            for index in (0, 1):
                if row[index].lstrip().startswith(("=", "+", "-", "@")) or row[
                    index
                ].startswith(("\t", "\r", "\n")):
                    row[index] = "'" + row[index]
            writer.writerow(row)
        return response
