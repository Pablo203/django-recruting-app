from django.db import models
from datetime import datetime

# Create your models here.
class Collection(models.Model):
    date = models.DateTimeField(default=datetime.now().strftime("%Y-%m-%d %H:%M"))
    filePath = models.CharField(max_length=200, default='')
    fileName = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.fileName