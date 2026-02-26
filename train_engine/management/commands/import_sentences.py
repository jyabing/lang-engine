from django.core.management.base import BaseCommand
from train_engine.models import SentenceItem, Course
import csv


class Command(BaseCommand):
    help = "Import sentences from CSV columns: zh,en,jp,kr,course(optional)"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **kwargs):
        file_path = kwargs["file"]

        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0

            for row in reader:
                item = SentenceItem.objects.create(
                    text_zh=row.get("zh", "") or "",
                    text_en=row.get("en", "") or "",
                    text_jp=row.get("jp", "") or "",
                    text_kr=row.get("kr", "") or "",
                )

                course_name = (row.get("course", "") or "").strip()
                if course_name:
                    course, _ = Course.objects.get_or_create(name=course_name)
                    course.items.add(item)

                count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {count} sentences"))