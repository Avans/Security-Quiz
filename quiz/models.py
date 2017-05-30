from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Answer(models.Model):
    user = models.ForeignKey(User)
    question = models.CharField(max_length=128)
    string = models.TextField()

    # Feedback
    points = models.IntegerField(null=True)
    comment = models.TextField(null=True)

    submitted = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return self.question + ": " + self.string

class LetsEncryptChallenge(models.Model):
    challenge = models.CharField(max_length=128)
    response = models.CharField(max_length=128)
    expiry_date = models.DateTimeField()
