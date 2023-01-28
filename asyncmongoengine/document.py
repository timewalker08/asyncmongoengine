
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, Union

from mongoengine.base import get_document
from mongoengine.document import Document
from pymongo import CursorType
from pymongo.client_session import ClientSession

from asyncmongoengine import connection


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
    _id = doc.pop("_id", None)
    if not _id:
        result = await collection.insert_one(doc)
        inserted_id = result.inserted_id
        return await type(self).find_one_async({"_id": inserted_id})
    else:
        await collection.replace_one({"_id": _id}, doc)
        return await type(self).find_one_async({"_id": _id})


async def find_one_async(cls, filter: Optional[Any] = None, *args: Any, **kwargs: Any):
    collection = cls._get_motor_collection()
    document = await collection.find_one(filter, *args, **kwargs)
    if not document:
        return None
    return cls._build_document(document)


def find(cls, *args, **kwargs):
    collection = cls._get_motor_collection()
    return collection.find(*args, **kwargs)


async def find_async(cls, *args, **kwargs):
    collection = cls._get_motor_collection()
    cursor = collection.find(*args, **kwargs)
    async for doc in cursor:
        yield cls._build_document(doc)


async def find_one_and_update_async(
    cls,
    filter: Mapping[str, Any],
    update: Union[Mapping[str, Any], Sequence[Mapping[str, Any]]],
    projection: Optional[Union[Mapping[str, Any], Iterable[str]]] = None,
    sort: Optional[Sequence[Tuple[str,
                                  Union[int, str, Mapping[str, Any]]]]] = None,
    upsert: bool = False,
    return_document: bool = False,
    array_filters: Optional[Sequence[Mapping[str, Any]]] = None,
    hint: Optional[Union[str, Sequence[Tuple[str,
                                             Union[int, str, Mapping[str, Any]]]]]] = None,
    session: Optional[ClientSession] = None,
    let: Optional[Mapping[str, Any]] = None,
    comment: Optional[Any] = None,
    **kwargs: Any
):
    collection = cls._get_motor_collection()
    doc = await collection.find_one_and_update(filter, update, projection, sort, upsert, return_document, array_filters, hint,
                                               session, let, comment, **kwargs)
    if not doc:
        return None
    return cls._build_document(doc)


async def count_async(cls, filter: Mapping[str, Any], session: Optional[ClientSession] = None, comment: Optional[Any] = None, **kwargs: Any):
    collection = cls._get_motor_collection()
    return await collection.count_documents(filter, session, comment, **kwargs)


async def update_many_async(cls, filter: Mapping[str, Any], update: Union[Mapping[str, Any], Sequence[Mapping[str, Any]]], upsert: bool = False, array_filters: Optional[Sequence[Mapping[str, Any]]] = None, bypass_document_validation: Optional[bool] = None, collation=None, hint: Optional[Union[str, Sequence[Tuple[str, Union[int, str, Mapping[str, Any]]]]]] = None, session: Optional[ClientSession] = None, let: Optional[Mapping[str, Any]] = None, comment: Optional[Any] = None):
    collection = cls._get_motor_collection()
    res = await collection.update_many(filter, update, upsert, array_filters, bypass_document_validation, collation, hint, session, let, comment)
    return res

async def delete_many_async(cls, filter: Mapping[str, Any], collation = None, hint: Optional[Union[str, Sequence[Tuple[str, Union[int, str, Mapping[str, Any]]]]]] = None, session: Optional[ClientSession] = None, let: Optional[Mapping[str, Any]] = None, comment: Optional[Any] = None):
    collection = cls._get_motor_collection()
    res = await collection.delete_many(filter, collation, hint, session, let, comment)
    return res


def apply_patch():
    setattr(Document, "_get_motor_collection",
            classmethod(_get_motor_collection))
    setattr(Document, "find_one_async", classmethod(find_one_async))
    setattr(Document, "_build_document", classmethod(_build_document))
    setattr(Document, "find_one_and_update_async",
            classmethod(find_one_and_update_async))
    setattr(Document, "find", classmethod(find))
    setattr(Document, "find_async", classmethod(find_async))
    setattr(Document, "save_async", save_async)
    setattr(Document, "count_async", classmethod(count_async))
    setattr(Document, "update_many_async", classmethod(update_many_async))
    setattr(Document, "delete_many_async", classmethod(delete_many_async))
