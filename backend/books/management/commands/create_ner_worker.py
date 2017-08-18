import logging

from connections import rabbitmq_channel
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from pika.exceptions import ConnectionClosed
from retrying import retry
from spacy.en import English
from collections import Counter

from books.models import (
    Book, Character
)

def retry_exception_handler(e):
    logging.warning("RETRY catched exception: %r. Another attempt..." % e)
    return isinstance(e, ConnectionClosed)

def get_persons_from_sent(sent):
    return Counter(list((word.lemma_ for word in sent if word.ent_type_ == 'PERSON')))


def get_all_persons(sents):
    MIN_COUNT = 3
    persons = Counter()
    for i, sent in enumerate(sents):
        persons.update(get_persons_from_sent(sent))
    return {person for person, number in persons.items() if number >= MIN_COUNT}


def get_characters(text):
    nlp = English()
    doc = nlp(text)
    return get_all_persons(doc.sents)


class Command(BaseCommand):
    @retry(retry_on_exception=retry_exception_handler,
           wait_fixed=1000,
           wrap_exception=True)
    def handle(self, *args, **options):
        conn, channel = rabbitmq_channel(settings.RABBIT_NER)

        def callback(ch, method, properties, body):
            logging.info("Working on book #%r" % body)
            try:
                book = Book.objects.get(id=body)

            except ObjectDoesNotExist:
                logging.error("Book #%s doesn't exist" % body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            try:
                book.character_set.all().delete()
                text = str(book.file.read())
                for person in get_characters(text):
                    Character.objects.create(name=person, book=book)
                book.stage = 2
                book.save()
            except Exception as e:
                logging.fatal("Book #%r NOT processed." % body, exc_info=True)
                print(e)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        # main logic
        channel.basic_consume(
            callback,
            queue=settings.RABBIT_NER,
            no_ack=False)

        logging.info("Start consumings events from queue: %s" % \
                    settings.RABBIT_NER)
        print(123)

        channel.start_consuming()
