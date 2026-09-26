import pytest

from apps.common.serializers import FileSerializer
from apps.common.tests.factories import FileFactory


@pytest.mark.django_db
def test_file_representation():
    file = FileFactory()
    assert FileSerializer(file).data == {
        "id": str(file.id),
        "url": file.url,
        "name": file.name,
    }
