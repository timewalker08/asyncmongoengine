
from asyncmongoengine import connection
from mongoengine.document import Document

def add(a, b):
    return a + b


def _get_motor_collection(self):
    return connection.db[self._get_collection_name()]

async def save_async(self):
    collection = self._get_motor_collection()
    doc = self.to_mongo()
    return await collection.insert_one(doc)

def apply_patch():
    setattr(Document, "_get_motor_collection", _get_motor_collection)
    setattr(Document, 'save_async', save_async)
