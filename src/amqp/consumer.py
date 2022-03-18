import pika


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


class Consumer:
    connection = None

    def __init__(self, config):
        self.config = config
        credentials = pika.PlainCredentials(config.get('user'), config.get('passwd'))
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(config.get('amqp_ip'),
                                                                            port=config.get('amqp_port'),
                                                                            credentials=credentials,
                                                                            heartbeat=600))
        self.channel = self.connection.channel()
        self.queue = config.get('queue')
        self.channel.queue_declare(queue=self.queue)

    def consume(self, cf):
        self.channel.basic_consume(self.queue,
                                   on_message_callback=cf,
                                   auto_ack=True)
        self.channel.start_consuming()

    def stop(self):
        self.channel.close()
        self.connection.close()
