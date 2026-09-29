from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.common.models import Files

pytestmark = pytest.mark.django_db
URL = "/api/v1/users/me/"


@pytest.fixture
def avatar():
    content = BytesIO()
    Image.new("RGB", (2, 2)).save(content, format="PNG")
    return SimpleUploadedFile(
        "avatar.png", content.getvalue(), content_type="image/png"
    )


def test_upload_persists_url_and_returns_it(auth_client, user, avatar, mocker):
    cloud = mocker.patch(
        "apps.common.service.cloudinary.uploader.upload",
        return_value={
            "secure_url": "https://example.com/avatar.png",
        },
    )
    response = auth_client.put(URL, {"avatar": avatar}, format="multipart")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.avatar == "https://example.com/avatar.png"
    assert response.data["avatar"] == user.avatar
    assert auth_client.get(URL).data["avatar"] == user.avatar
    assert Files.objects.filter(url=user.avatar).exists()
    cloud.assert_called_once()


@pytest.mark.parametrize(
    "failure", ["File is too large. Maximum file size is 5 MB.", "Upload failed"]
)
def test_upload_failure_returns_400_without_profile_changes(
    auth_client, user, avatar, mocker, failure
):
    user.avatar = "https://example.com/old.png"
    user.save()
    previous_name = user.first_name
    mocker.patch(
        "apps.users.serializers.FileService.upload_file_to_cloud",
        side_effect=ValueError(failure),
    )
    response = auth_client.put(
        URL, {"avatar": avatar, "full_name": "New Name"}, format="multipart"
    )
    assert response.status_code == 400
    assert "avatar" in response.data
    user.refresh_from_db()
    assert user.avatar == "https://example.com/old.png"
    assert user.first_name == previous_name


def test_invalid_image_never_uploads(auth_client, mocker):
    upload = mocker.patch("apps.users.serializers.FileService.upload_file_to_cloud")
    invalid = SimpleUploadedFile("bad.png", b"not an image", content_type="image/png")
    response = auth_client.put(URL, {"avatar": invalid}, format="multipart")
    assert response.status_code == 400
    assert "avatar" in response.data
    upload.assert_not_called()


def test_omitted_avatar_is_preserved_and_null_clears_it(auth_client, user):
    user.avatar = "https://example.com/old.png"
    user.save()
    response = auth_client.put(
        URL, {"full_name": "Nancy Solanki", "gender": "FE"}, format="json"
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert (user.first_name, user.last_name, user.gender) == ("Nancy", "Solanki", "FE")
    assert user.avatar == "https://example.com/old.png"
    response = auth_client.put(URL, {"avatar": None}, format="json")
    assert response.status_code == 200
    assert response.data["avatar"] is None
    user.refresh_from_db()
    assert user.avatar == ""


def test_full_name_respects_model_limits(auth_client):
    response = auth_client.put(URL, {"full_name": "x" * 201}, format="json")
    assert response.status_code == 400
    assert "full_name" in response.data


def test_profile_settings_persist(auth_client, user):
    payload = {
        "public_profile": True,
        "search_engine_visibility": True,
        "share_learning_activity": True,
        "language": "hi",
        "bio": "Learning Python",
    }
    response = auth_client.put(URL, payload, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    fetched = auth_client.get(URL)
    for field, value in payload.items():
        assert getattr(user, field) == value
        assert response.data[field] == value
        assert fetched.data[field] == value


def test_profile_settings_defaults(user):
    assert user.public_profile is False
    assert user.search_engine_visibility is False
    assert user.share_learning_activity is False
    assert user.language == "en"
    assert user.bio == ""
