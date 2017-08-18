from django.db import models
from django.contrib.postgres.fields import ArrayField


SEX_CHOICES = (
    (0, 'Female'),
    (1, 'Male'),
    (2, 'Undefined')
)


class Book(models.Model):
    name = models.TextField()
    file = models.FileField(null=False, upload_to='files')
    stage = models.IntegerField(default=0)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.name


class Character(models.Model):
    name = models.TextField()
    book = models.ForeignKey('Book')
    sex = models.IntegerField(choices=SEX_CHOICES, default=SEX_CHOICES[2][0])

    def __repr__(self):
        return "{} [{}]".format(self.name, self.book)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return "{} [{}]".format(self.name, self.book)


class PartOfBody(models.Model):
    part = models.TextField()
    description = ArrayField(models.TextField())
    sentence_number = models.IntegerField()
    word_number = models.IntegerField()
    book = models.ForeignKey('Book')


class CharacterPartOfBody(models.Model):
    part = models.TextField()
    description = ArrayField(models.TextField())
    character = models.ForeignKey('Character')


class Trait(models.Model):
    name = models.TextField()
    sentence_number = models.IntegerField()
    word_number = models.IntegerField()
    book = models.ForeignKey('Book')


class CharacterTrait(models.Model):
    name = models.TextField()
    character = models.ForeignKey('Character')
