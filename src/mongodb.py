import pymongo

class MongoDB(object):
    DATABASE = None

    @staticmethod
    def __init__(config):
        MongoDB.config = config
        client = pymongo.MongoClient(
            host=config.get('host'),
            serverSelectionTimeoutMS=config.get('timeout'),
            username=config.get('user'),
            password=config.get('passwd')
        )
        MongoDB.DATABASE = client[config.get('database')]

    @staticmethod
    def insert(colleciton, data):
        MongoDB.DATABASE[colleciton].insert(data)

    @staticmethod
    def find(collection, query):
        return MongoDB.DATABASE[collection].find(query)