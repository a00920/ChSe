from django.conf.urls import url

from books.views import (BookListView, NerCommandView, BookView, CharacterConfirmView,
                         CharacterPartBodyExtractorView)

urlpatterns = [
    url(r'^ner/(?P<book_id>[0-9]+?)$', NerCommandView.as_view(), name='ner'),
    url(r'^book/(?P<book_id>[0-9]+?)$', BookView.as_view(), name='ner'),
    url(r'^character_confirm$', CharacterConfirmView.as_view(), name='character-confirm'),
    url(r'^part_body_extractor_confirm$', CharacterPartBodyExtractorView.as_view(), name='character-confirm'),
    url(r'^$', BookListView.as_view(), name='book-list'),
]