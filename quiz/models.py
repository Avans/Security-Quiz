from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Answer(models.Model):
    user = models.ForeignKey(User)
    question = models.CharField(max_length=128)
    string = models.TextField()

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return self.question + ": " + self.string