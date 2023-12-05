from django.db import models

# Create your models here.


class Candle(models.Model):
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    date = models.DateTimeField()


class MyModel(models.Model):
    csv = models.FileField(upload_to='csv/')
    json = models.FileField(upload_to='json/')
