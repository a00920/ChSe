import logging

from connections import rabbitmq_channel
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from pika.exceptions import ConnectionClosed
from retrying import retry
from spacy.en import English
from collections import Counter, defaultdict
from libs.predicat_solver.predicat_solver import Predicate, solve_system, solve_system_with_GA

from books.models import (
    Book, Character
)

def retry_exception_handler(e):
    logging.warning("RETRY catched exception: %r. Another attempt..." % e)
    return isinstance(e, ConnectionClosed)


def get_equation(sents, lemma2character):
    row = []
    for sent in sents:
        for word in sent:
            if word.lemma_ in lemma2character:
                row.append(lemma2character[word.lemma_])
    return row


def get_system(sents, lemma2character, window=2):
    system = []
    last_he = -window
    last_she = -window
    used_ids = set()
    for i in range(len(sents)):
        sent = sents[i]

        for j in range(len(sent)):
            sents_in_window = sents[max(0, i - window): i] + [sents[i][:j]]
            if sent[j].lower_ == 'he' or sent[j].lower_ == 'his' or sent[j].lower_ == 'him':
                if i - last_he <= window:
                    last_he = i
                    continue

                last_he = i
                row = get_equation(sents_in_window, lemma2character)
                used_ids.update(row)
                print(row, 'T', i)
                if row:
                    system.append(Predicate(Predicate.POSITIVE_TYPE, row))
            if sent[j].lower_ == 'she' or sent[j].lower_ == 'her':
                if i - last_she <= window:
                    last_she = i
                    continue
                last_she = i
                row = get_equation(sents_in_window, lemma2character)
                used_ids.update(row)
                print(row, 'F', i)
                if row:
                    system.append(Predicate(Predicate.NEGATIVE_TYPE, row))
    return system, used_ids


def get_characters_info(text, characters):
    nlp = English()
    doc = nlp(text)
    lemma2character = {}
    short_id2id = {}
    for i, character in enumerate(characters):
        lemma2character[character.name] = i
        short_id2id[i] = character.id
    system, used_ids = get_system(list(doc.sents), lemma2character)
    solution = solve_system_with_GA(system)

    UNDEFINED_SEX = 2
    character_id2sex = defaultdict(lambda: UNDEFINED_SEX)
    print(used_ids)
    for i, sex in enumerate(solution):
        if i in used_ids:
            character_id2sex[short_id2id[i]] = sex
    return character_id2sex


class Command(BaseCommand):
    @retry(retry_on_exception=retry_exception_handler,
           wait_fixed=1000,
           wrap_exception=True)
    def handle(self, *args, **options):
        conn, channel = rabbitmq_channel(settings.RABBIT_PREDICAT_SOLVER)

        def callback(ch, method, properties, body):
            logging.info("Working on book #%r" % body)
            try:
                book = Book.objects.get(id=body)

            except ObjectDoesNotExist:
                logging.error("Book #%s doesn't exist" % body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            try:
                text = str(book.file.read())
                characters = book.character_set.all()
                character_id2sex = get_characters_info(text, characters)
                for character in characters:
                    character.sex = character_id2sex[character.id]
                    character.save()
                book.stage = 4
                book.save()
            except Exception as e:
                logging.fatal("Book #%r NOT processed." % body, exc_info=True)
                print(e)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        # main logic
        channel.basic_consume(
            callback,
            queue=settings.RABBIT_PREDICAT_SOLVER,
            no_ack=False)

        logging.info("Start consumings events from queue: %s" % \
                    settings.RABBIT_PREDICAT_SOLVER)

        channel.start_consuming()
