from django.core.management.base import BaseCommand
from django.db import transaction # Import transaction for better performance
import re
from collections import Counter
from corpusapp.models import Entry, WordFrequency

class Command(BaseCommand):
    help = 'Calculates and displays the frequency of all words in the Entry.isizulu fields.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting IsiZulu Word Frequency Analysis ---"))
        all_isizulu_texts = Entry.objects.all().values_list('isizulu', flat=True)
        all_words = []
        for text in all_isizulu_texts:
            text = text.lower()
            words = re.findall(r'\b\w+\b', text)
            all_words.extend(words)

        word_counts = Counter(all_words)

        self.stdout.write("Saving new word frequency data...")
        WordFrequency.objects.all().delete()
        words_to_create = []
        for word, count in word_counts.items():
            words_to_create.append(WordFrequency(word=word, count=count))

        WordFrequency.objects.bulk_create(words_to_create)

        self.stdout.write(self.style.SUCCESS("--- Word Frequency Data Saved Successfully ---"))
        self.stdout.write(self.style.SUCCESS(f"Total unique words saved: {len(word_counts)}"))
