from django.contrib import admin

from books.models import Book, Character, CharacterPartOfBody, CharacterTrait, PartOfBody, Trait

admin.site.register(Book)
admin.site.register(Character)

admin.site.register(CharacterPartOfBody)
admin.site.register(CharacterTrait)
admin.site.register(PartOfBody)
admin.site.register(Trait)

