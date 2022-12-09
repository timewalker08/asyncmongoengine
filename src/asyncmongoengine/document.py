
from connection import client, db
from mongoengine.document import Document

def add(a, b):
    return a + b

@classmethod
def _get_motor_collection(cls):
    return db[cls._get_collection_name()]

async def save_async(self):
    collection = self._get_motor_collection()
    doc = self.to_mongo()
    await collection.insert_one(doc)

setattr(Document, 'save_async', save_async)