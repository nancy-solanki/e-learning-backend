from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from opensearchpy.helpers import bulk

from apps.course.models import Course
from apps.course.search import course_document, get_client


class Command(BaseCommand):
    help = "Create the course OpenSearch index if needed and rebuild its documents."

    def handle(self, *args, **options):
        if not getattr(settings, "OPENSEARCH_ENABLED", False):
            raise CommandError("OpenSearch is not enabled in the active settings.")

        client = get_client()
        index = settings.OPENSEARCH_INDEX
        if not client.indices.exists(index=index):
            client.indices.create(
                index=index,
                body={
                    "mappings": {
                        "properties": {
                            "title": {"type": "text"},
                            "short_description": {"type": "text"},
                            "long_description": {"type": "text"},
                            "requirements": {"type": "text"},
                            "learn_description_points": {"type": "text"},
                            "categories": {"type": "text"},
                            "tags": {"type": "text"},
                            "instructor": {"type": "text"},
                            "status": {"type": "keyword"},
                            "deleted": {"type": "boolean"},
                        }
                    }
                },
            )
        else:
            client.delete_by_query(
                index=index,
                body={"query": {"match_all": {}}},
                refresh=True,
                conflicts="proceed",
            )

        courses = (
            Course.objects.select_related("instructor")
            .prefetch_related("categories", "tags")
            .iterator(chunk_size=500)
        )
        actions = (
            {
                "_op_type": "index",
                "_index": index,
                "_id": str(course.pk),
                "_source": course_document(course),
            }
            for course in courses
        )
        _, errors = bulk(client, actions, raise_on_error=False, refresh=True)
        if errors:
            raise CommandError(f"OpenSearch reported {len(errors)} indexing errors.")
        self.stdout.write(self.style.SUCCESS("Course index rebuilt successfully."))
