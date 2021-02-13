import pika
import configparser


class Publisher:

    def __init__(self, config):
        self.config = config
        credentials = pika.PlainCredentials(config.get('user'), config.get('passwd'))
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(config.get('amqp_ip'), credentials=credentials))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='testing')

    def publish(self, message):
        try:
            self.channel.basic_publish(exchange='', routing_key='testing', body=message)
        except Exception as e:
            print(e)
        print("published")
