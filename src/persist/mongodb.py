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
        if config.get('debug'):
            MongoDB.DATABASE = client[config.get('debug_database')]
        else:
            MongoDB.DATABASE = client[config.get('database')]

    @staticmethod
    def insert(collection, data):
        MongoDB.DATABASE[collection].insert(data)

    @staticmethod
    def update(collection, query, update):
        MongoDB.DATABASE[collection].update(query, update, upsert=True)

    @staticmethod
    def find(collection, query):
        return list(MongoDB.DATABASE[collection].find(query))

    @staticmethod
    def find_limit_ordered(collection, query, limit):
        return list(MongoDB.DATABASE[collection].find(query).limit(limit).sort("date", -1))
    
    @staticmethod
    def update_one(collection, query, update):
        return MongoDB.DATABASE[collection].update(query, update)
    
    @staticmethod
    def insert_one(collection, data):
        MongoDB.DATABASE[collection].insert_one(data)
