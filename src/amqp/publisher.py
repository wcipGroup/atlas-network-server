import pika


class Publisher:

    def __init__(self, config):
        try:
            self.config = config
            credentials = pika.PlainCredentials(config.get('user'), config.get('passwd'))
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(config.get('amqp_ip'),
                                                                                credentials=credentials,
                                                                                heartbeat=600))
            self.channel = self.connection.channel()
            self.queue = config.get('queue')
            self.channel.queue_declare(queue=self.queue)
        except Exception as e:
            raise e

    def publish(self, message):
        try:
            self.channel.basic_publish(exchange='', routing_key=self.queue, body=message)
            print("published")
        except Exception as e:
            print(e)

    def stop(self):
        self.channel.close()
        self.connection.close()
