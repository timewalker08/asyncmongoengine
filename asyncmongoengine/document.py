
import re

import pymongo

from asyncmongoengine.base.document import BaseDocument
from asyncmongoengine.base.errors import NotUniqueError, OperationError
from asyncmongoengine.base.metaclasses import (DocumentMetaclass,
                                               TopLevelDocumentMetaclass)
from asyncmongoengine.connection import DEFAULT_CONNECTION_NAME, get_db
from asyncmongoengine.context_managers import set_write_concern


class EmbeddedDocument(BaseDocument, metaclass=DocumentMetaclass):

    __slots__ = ("_instance",)

    my_metaclass = DocumentMetaclass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance = None
        self._changed_fields = []

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    
class Document(BaseDocument, metaclass=TopLevelDocumentMetaclass):

    my_metaclass = TopLevelDocumentMetaclass

    __slots__ = ("__objects",)

    @property
    def pk(self):
        return None

    async def save_async(
        self,
        force_insert=False,
        validate=True,
        clean=True,
        write_concern=None,
        _refs=None,
        **kwargs
    ):
        if validate:
            self.validate(clean=clean)

        doc = self.to_mongo()

        if write_concern is None:
            write_concern = {}

        try:
            # Save a new document or update an existing one
            object_id = await self._save_create_async(doc, force_insert, write_concern)

        except pymongo.errors.DuplicateKeyError as err:
            message = "Tried to save duplicate unique keys (%s)"
            raise NotUniqueError(message % err)
        except pymongo.errors.OperationFailure as err:
            message = "Could not save document (%s)"
            if re.match("^E1100[01] duplicate key", str(err)):
                # E11000 - duplicate key error index
                # E11001 - duplicate key on update
                message = "Tried to save duplicate unique keys (%s)"
                raise NotUniqueError(message % err)
            raise OperationError(message % err)

        return self


    async def _save_create_async(self, doc, force_insert, write_concern):
        """Save a new document.

        Helper method, should only be used inside save().
        """
        collection = self._get_collection()

        with set_write_concern(collection, write_concern) as wc_collection:
            if "_id" in doc:
                raw_object = await wc_collection.find_one_and_replace(
                    filter={"_id": doc["_id"]},
                    replacement=doc
                )
                if raw_object:
                    return doc["_id"]

            object_id = (await wc_collection.insert_one(doc)).inserted_id

        return object_id


    def to_mongo(self, *args, **kwargs):
        data = super().to_mongo(*args, **kwargs)

        # If '_id' is None, try and set it from self._data. If that
        # doesn't exist either, remove '_id' from the SON completely.
        if data["_id"] is None:
            if self._data.get("id") is None:
                del data["_id"]
            else:
                data["_id"] = self._data["id"]

        return data

    @classmethod
    def _get_db(cls):
        """Some Model using other db_alias"""
        return get_db(cls._meta.get("db_alias", DEFAULT_CONNECTION_NAME))

    @classmethod
    def _get_collection(cls):
        """Return the PyMongo collection corresponding to this document.

        Upon first call, this method:
        1. Initializes a :class:`~pymongo.collection.Collection` corresponding
           to this document.
        2. Creates indexes defined in this document's :attr:`meta` dictionary.
           This happens only if `auto_create_index` is True.
        """
        if not hasattr(cls, "_collection") or cls._collection is None:
            db = cls._get_db()
            collection_name = cls._get_collection_name()
            cls._collection = db[collection_name]

        return cls._collection
