import logging

from connections import rabbitmq_channel
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from pika.exceptions import ConnectionClosed
from retrying import retry
from spacy.en import English


from books.models import (
    Book, PartOfBody
)

PART_OF_BODY = {
    'hair',
    'body',
    'leg',
    'eye',
    'tail',
    'head',
    'nose',
    'ear',
    'eyebrows'
}

def retry_exception_handler(e):
    logging.warning("RETRY catched exception: %r. Another attempt..." % e)
    return isinstance(e, ConnectionClosed)


def get_parts_of_body(sents):
    parts_of_body = []
    for sent_number, sent in enumerate(sents):
        print(sent_number, len(sents))
        for word_number, word in enumerate(sent):
            if word.lemma_ in PART_OF_BODY and get_info_from_body_type(word) and get_parent(word):
                parts_of_body.append((word.lemma_, get_info_from_body_type(word), word_number,
                                      sent_number))

    return parts_of_body


def get_info_from_body_type(node):
    return [child for child in node.children if child.dep_ == 'amod']


def get_characters_info(text):
    nlp = English()
    doc = nlp(text)
    parts_of_body = get_parts_of_body(list(doc.sents))

    return parts_of_body


class Command(BaseCommand):
    @retry(retry_on_exception=retry_exception_handler,
           wait_fixed=1000,
           wrap_exception=True)
    def handle(self, *args, **options):
        conn, channel = rabbitmq_channel(settings.RABBIT_PART_BODY_SELECTOR)

        def callback(ch, method, properties, body):
            logging.info("Working on book #%r" % body)
            try:
                book = Book.objects.get(id=body)

            except ObjectDoesNotExist:
                logging.error("Book #%s doesn't exist" % body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            try:
                print('-----------')
                text = str(book.file.read())
                #PartOfBody.objects.filter(book=book).delete()
                parts_of_body = get_characters_info(text)
                print(parts_of_body)
                for name, description, word_number, sent_number in parts_of_body:
                    PartOfBody.objects.create(part=name, description=description,
                                              word_number=word_number, sentence_number=sent_number,
                                              book=book)
            except Exception as e:
                logging.fatal("Book #%r NOT processed." % body, exc_info=True)
                print(e)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        # main logic
        channel.basic_consume(
            callback,
            queue=settings.RABBIT_PART_BODY_SELECTOR,
            no_ack=False)

        logging.info("Start consumings events from queue: %s" % \
                    settings.RABBIT_PART_BODY_SELECTOR)

        channel.start_consuming()


def get_parent(node):
    p1 = [child for child in node.children if child.dep_ == 'poss']
    p2 = [child for child in node.head.children if child.dep_ == 'poss']
    parent = node.head
    #while parent.pos_ != 'VERB':
    #    parent = parent.head
    #p3 = [child for child in parent.children if child.dep_ == 'nsubj']
    if (p1 + p2 ):
        return (p1 + p2)[0]
    return None
