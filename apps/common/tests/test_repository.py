import uuid

import pytest

from apps.common.models import Files
from apps.common.repository import FileRepository

pytestmark = pytest.mark.django_db


def test_repository_lifecycle():
    file = FileRepository.create_file(
        "https://example.com/image.png", "image.png", "image/png", 4
    )
    assert FileRepository.get_file_by_id(file.id) == file
    assert list(FileRepository.get_all_files()) == [file]
    assert FileRepository.delete_file(file.id) is True
    assert FileRepository.get_file_by_id(file.id) is None
    assert FileRepository.delete_file(file.id) is False
    assert not Files.objects.exists()


def test_unknown_file():
    assert FileRepository.get_file_by_id(uuid.uuid4()) is None
    assert FileRepository.delete_file(uuid.uuid4()) is False
