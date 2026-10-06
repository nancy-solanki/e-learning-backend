"""Admin invitations and recipient-owned password setup."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.auth.services import generate_uid
from apps.core.permission import IsSuperuser
from apps.core.schema import DetailSerializer, MessageSerializer
from apps.core.services import send_email

User = get_user_model()


class InvitationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "apps.users.invitations.InvitationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return (
            super()._make_hash_value(user, timestamp)
            + str(user.status)
            + str(user.is_active)
            + str(user.deleted_at)
        )


invitation_token = InvitationTokenGenerator()


def is_pending_invitation(user):
    return (
        user.status == User.Status.PENDING
        and not user.is_active
        and user.deleted_at is None
        and not user.has_usable_password()
    )


class InvitationDeliveryError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Invitation email could not be queued. Please try again."


def send_invitation(user):
    base = (
        settings.FRONTEND_URL
        if user.groups.filter(name="student").exists()
        else settings.ADMIN_URL
    ).rstrip("/")
    link = f"{base}/accept-invite/{generate_uid(user)}/{invitation_token.make_token(user)}/"
    try:
        html = render_to_string("user/invitation.html", {"link": link})
        # The worker sends the email; only broker failures reach this request.
        send_email.delay(
            {
                "subject": "You are invited to Learnify",
                "body": strip_tags(html),
                "html_body": html,
                "to_email": user.email,
            }
        )
    except Exception as exc:
        raise InvitationDeliveryError() from exc


class InviteUserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=("student", "instructor", "admin"), default="student"
    )

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "role")

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        value = value.lower()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError(
                {key: "This field is not accepted." for key in sorted(unknown)}
            )
        return attrs

    def create(self, validated_data):
        role = validated_data.pop("role")
        try:
            with transaction.atomic():
                user = User(
                    **validated_data, status=User.Status.PENDING, is_active=False
                )
                user.set_unusable_password()
                user.save()
                user.groups.add(Group.objects.get_or_create(name=role)[0])
                send_invitation(user)
                return user
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"detail": "Email or username already exists."}
            ) from exc


class InvitationResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    status = serializers.CharField()
    message = serializers.CharField()


class InviteUserView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsSuperuser)
    serializer_class = InviteUserSerializer

    @extend_schema(
        tags=["Users"],
        description=(
            "Invite a student, instructor, or admin. Administrator access "
            "required; the recipient sets their own password via an emailed "
            "link."
        ),
        responses={201: InvitationResponseSerializer, 503: DetailSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": str(user.pk),
                "email": user.email,
                "status": "PENDING",
                "message": "Invitation sent successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class ResendInvitationView(GenericAPIView):
    permission_classes = (IsAuthenticated, IsSuperuser)
    serializer_class = MessageSerializer
    queryset = User.objects.all()

    @extend_schema(
        tags=["Users"],
        description=(
            "Resend a pending invitation and invalidate the previous link. "
            "Administrator access required."
        ),
        request=None,
        responses={200: MessageSerializer, 503: DetailSerializer},
    )
    def post(self, request, pk):
        with transaction.atomic():
            self.queryset = self.queryset.select_for_update()
            user = self.get_object()
            if not is_pending_invitation(user):
                raise serializers.ValidationError(
                    {"detail": "Only pending invitations can be resent."}
                )
            # Rotate the unusable password marker to invalidate previous links.
            user.set_unusable_password()
            user.save(update_fields=("password", "updated_at"))
            send_invitation(user)
        return Response({"message": "Invitation sent successfully"})


class AcceptInvitationSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=128
    )

    def save(self, **kwargs):
        invalid = {"detail": "Invitation link is invalid or expired."}
        with transaction.atomic():
            try:
                uid = force_str(urlsafe_base64_decode(self.context["uid"]))
                user = User.objects.select_for_update().get(pk=uid)
            except (
                ValueError,
                TypeError,
                UnicodeDecodeError,
                DjangoValidationError,
                User.DoesNotExist,
            ):
                raise serializers.ValidationError(invalid)
            if not is_pending_invitation(user) or not invitation_token.check_token(
                user, self.context["token"]
            ):
                raise serializers.ValidationError(invalid)
            password = self.validated_data["password"]
            try:
                validate_password(password, user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": exc.messages}) from exc
            user.set_password(password)
            user.password_changed_at = timezone.now()
            user.status = User.Status.ACTIVE
            user.is_active = True
            user.save(
                update_fields=(
                    "password",
                    "password_changed_at",
                    "status",
                    "is_active",
                    "updated_at",
                )
            )
            return user


class AcceptInvitationView(GenericAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = AcceptInvitationSerializer

    @extend_schema(
        tags=["Authentication"],
        description=(
            "Accept an invitation using the emailed UID and single-use token, "
            "and set a password."
        ),
        responses={200: MessageSerializer},
    )
    def post(self, request, uid, token):
        serializer = self.get_serializer(
            data=request.data, context={"uid": uid, "token": token}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Account activated successfully"})
