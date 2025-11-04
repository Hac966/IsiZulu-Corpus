from django.contrib import admin
from .models import Entry, AttireBase, CeremoniesBase, CuisineBase, HistoryBase, UserInfo, QuizBase, QuizScores, WordFrequency

# Register your models here.
admin.site.site_header = "Corpus Administration"
admin.site.site_title = "Corpus Admin Portal"

admin.site.register(Entry)
admin.site.register(AttireBase)
admin.site.register(CeremoniesBase)
admin.site.register(CuisineBase)
admin.site.register(HistoryBase)
admin.site.register(UserInfo)
admin.site.register(QuizBase)
admin.site.register(QuizScores)

admin.site.register(WordFrequency)