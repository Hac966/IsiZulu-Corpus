from unittest.mock import DEFAULT

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Create your models here.
STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Disapproved', 'Disapproved'),
)

class Entry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    isizulu = models.CharField(max_length=10000)
    english = models.CharField(max_length=20000)
    extract = models.CharField(max_length=90000)
    isixhosa = models.CharField(max_length=2000, blank=True, null=True)
    isipedi = models.CharField(max_length=2000, blank=True, null=True)
    learn_more = models.URLField(max_length=200, default="")
    word_usage = models.CharField(max_length=200)
    commonly = models.CharField(max_length=200)
    word_frequency = models.IntegerField(default = 0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    word = models.IntegerField(default=0)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_entries',  # A way to access the entries a user likes: user.favorite_entries.all()
        blank=True
    )

    def __str__(self):
        return self.isizulu



class CeremoniesBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    heading = models.CharField(max_length=200)
    extract = models.TextField(max_length=700, blank=True)
    learnMore = models.URLField(max_length=200, blank=True, null=True)
    picture = models.ImageField(upload_to='corpusapp/user/categories/ceremonies/')
    file = models.FileField(upload_to='corpusapp/user/categories/ceremonies/files', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.heading

class AttireBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    heading = models.CharField(max_length= 200)
    extract = models.TextField(max_length=700, blank=True)
    learnMore = models.URLField(max_length=200, blank=True, null=True)
    picture = models.ImageField(upload_to='corpusapp/user/categories/attire/')
    file = models.FileField(upload_to='corpusapp/user/categories/attire/files', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.heading

class CuisineBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    heading = models.CharField(max_length=200)
    extract = models.TextField(max_length=700, blank=True)
    learnMore = models.URLField(max_length=200, blank=True, null=True)
    picture = models.ImageField(upload_to='corpusapp/user/categories/cuisine/', blank=True, null=True)
    file = models.FileField(upload_to='corpusapp/user/categories/cuisine/files', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.heading

class HistoryBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    heading = models.CharField(max_length=200)
    extract = models.TextField(max_length=7000000, blank=True)
    picture = models.ImageField(upload_to='corpusapp/user/categories/history/images')
    file = models.FileField(upload_to='corpusapp/user/categories/history/files', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.heading

class QuizBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    question = models.CharField(max_length=900)
    answer = models.TextField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.question

class UserInfo(AbstractUser):
    pass

    def __str__(self):
        return self.username

class QuizScores(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)

    def __str__(self):


        if self.user:
            return f'{self.user.username} - Score: {self.score}/{self.max_score}'
        else:
            # Handle the case where 'user' is null/blank (as per your model definition)
            return f'Anonymous User - Score: {self.score}/{self.max_score}'


class WordFrequency(models.Model):
    word = models.CharField(max_length=255, unique=True)
    count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.word}: {self.count}"

    class Meta:
        ordering = ['-count']



