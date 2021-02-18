import pika


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


class Consumer:
    connection = None

    def __init__(self, config):
        self.config = config
        credentials = pika.PlainCredentials(config.get('user'), config.get('passwd'))
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(config.get('amqp_ip'), credentials=credentials))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='testing')

    def consume(self, cf):
        self.channel.basic_consume('testing',
                                   on_message_callback=cf)
        self.channel.start_consuming()

    def stop(self):
        self.channel.close()
        self.connection.close()
