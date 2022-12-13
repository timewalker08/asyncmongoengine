
from typing import Any, Optional

from mongoengine.document import Document

from asyncmongoengine import connection
from mongoengine.base import get_document
from pymongo import CursorType


def add(a, b):
    return a + b


def _get_motor_collection(cls):
    return connection.db[cls._get_collection_name()]


def _build_document(cls, doc):
    if "_cls" in doc:
        return get_document(doc["_cls"])._from_son(doc)
    else:
        return cls._from_son(doc)


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
    return cls._build_document(document)


def find(cls, *args, **kwargs):
    collection = cls._get_motor_collection()
    return collection.find(*args, **kwargs)


async def find_async(cls, *args, **kwargs):
    collection = cls._get_motor_collection()
    cursor = collection.find(*args, **kwargs)
    async for doc in cursor:
        yield cls._build_document(doc)


def apply_patch():
    setattr(Document, "_get_motor_collection",
            classmethod(_get_motor_collection))
    setattr(Document, "find_one_async", classmethod(find_one_async))
    setattr(Document, "_build_document", classmethod(_build_document))
    setattr(Document, "find", classmethod(find))
    setattr(Document, "find_async", classmethod(find_async))
    setattr(Document, 'save_async', save_async)
