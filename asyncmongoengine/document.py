
from typing import Any, Optional

from mongoengine.document import Document

from asyncmongoengine import connection
from mongoengine.base import get_document


def add(a, b):
    return a + b


def _get_motor_collection(cls):
    return connection.db[cls._get_collection_name()]

async def save_async(self):
    collection = type(self)._get_motor_collection()
    doc = self.to_mongo()
    result = await collection.insert_one(doc)
    inserted_id = result.inserted_id
    return await type(self).find_one_async({"_id": inserted_id})

async def find_one_async(cls, filter: Optional[Any] = None, *args: Any, **kwargs: Any):
    collection = cls._get_motor_collection()
    document = await collection.find_one(filter, *args, **kwargs)
    if not document:
        raise cls.DoesNotExist()
    if "_cls" in document:
        return get_document(document["_cls"])._from_son(document)
    else:
        return cls._from_son(document)

def apply_patch():
    setattr(Document, "_get_motor_collection", classmethod(_get_motor_collection))
    setattr(Document, "find_one_async", classmethod(find_one_async))
    setattr(Document, 'save_async', save_async)
