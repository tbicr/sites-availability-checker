import aiokafka
from aiokafka.helpers import create_ssl_context

from service import config
from service.entities import Event


async def kafka_producer_factory(config):
    if config["ssl_context"]:
        config = dict(config, ssl_context=create_ssl_context(**config["ssl_context"]))
    producer = aiokafka.AIOKafkaProducer(**config)
    await producer.start()
    return producer


async def kafka_consumer_factory(topic, config):
    if config["ssl_context"]:
        config = dict(config, ssl_context=create_ssl_context(**config["ssl_context"]))
    consumer = aiokafka.AIOKafkaConsumer(topic, **config)
    await consumer.start()
    return consumer


async def put_results_to_kafka(producer: aiokafka.AIOKafkaProducer, event: Event):
    await producer.send_and_wait(config.KAFKA_TOPIC, event.serialize())
