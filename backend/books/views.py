from django.utils import timezone
from django.views.generic.list import ListView
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from connections import rabbitmq_channel
from django.conf import settings
from django.shortcuts import redirect


from books.models import Book


class BookListView(ListView):

    model = Book

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

class BookView(TemplateView):
    template_name='books/book.html'

    def get_context_data(self, book_id):
        context = super(TemplateView, self).get_context_data()
        context['now'] = timezone.now()
        context['book'] = Book.objects.get(id=book_id)
        return context


class CharacterConfirmView(View):
    def post(self, request, *args, **kwargs):
        characters_ids = set(request.POST.getlist('characters_ids'))
        book_id = request.POST['book_id']
        book = Book.objects.get(id=book_id)
        book.stage = 3
        book.save()
        for character in book.character_set.all():
            if str(character.id) not in characters_ids:
                character.delete()
        conn, channel = rabbitmq_channel(settings.RABBIT_PREDICAT_SOLVER)
        channel.basic_publish(
            exchange='',
            routing_key=settings.RABBIT_PREDICAT_SOLVER,
            body=str(book_id))

        conn.close()

        return redirect('/book/{}'.format(book_id))


class CharacterPartBodyExtractorView(View):
    def post(self, request, *args, **kwargs):
        book_id = request.POST['book_id']

        conn, channel = rabbitmq_channel(settings.RABBIT_PART_BODY_SELECTOR)
        channel.basic_publish(
            exchange='',
            routing_key=settings.RABBIT_PART_BODY_SELECTOR,
            body=str(book_id))

        conn.close()

        return redirect('/book/{}'.format(book_id))


class NerCommandView(ListView):
    def get(self, request, book_id):
        conn, channel = rabbitmq_channel(settings.RABBIT_NER)

        # we want avoid race conditions here
        book = Book.objects.get(id=book_id)
        book.stage = 1
        book.save()

        channel.basic_publish(
            exchange='',
            routing_key=settings.RABBIT_NER,
            body=str(book_id))

        conn.close()
        return redirect('/')