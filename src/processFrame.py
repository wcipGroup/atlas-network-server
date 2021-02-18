import pika
from src.amqp.consumer import Consumer
import configparser

consumer = None


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


if __name__ == "__main__":
    try:
        print("start")
        config = configparser.ConfigParser()
        config.read('../config.ini')
        config_amqp = config['AMQP']
        consumer = Consumer(config_amqp)
    except Exception as e:
        print(e)
        raise exit(1)
    try:
        consumer.consume(callback)
    except KeyboardInterrupt:
        consumer.stop()
        print("EXIT")
