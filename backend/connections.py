import logging

import pika
from pika.exceptions import ConnectionClosed
from retrying import retry

from django.conf import settings


logger = logging.getLogger("connections")

def retry_exception_handler(e):
    logger.warn("RETRY catched exception: %r. Another attempt..." % e)
    return isinstance(e, ConnectionClosed)


# exponential backoff
@retry(retry_on_exception=retry_exception_handler,
       wrap_exception=True,
       wait_exponential_multiplier=1000,
       wait_exponential_max=10000,
       stop_max_delay=30000)
def rabbitmq_connection():
    credentials = pika.PlainCredentials(settings.RABBIT_USER, settings.RABBIT_PASS)
    parameters = pika.ConnectionParameters(
        settings.RABBIT_HOST, settings.RABBIT_PORT,
        '/', credentials)
    return pika.BlockingConnection(parameters)


def rabbitmq_channel(name):
    """Return tuple (`connection`, `channel`) to RabbitMQ"""

    connection = rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=name)

    return connection, channel