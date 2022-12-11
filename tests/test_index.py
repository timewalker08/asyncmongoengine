import unittest

import motor.motor_asyncio
from mongoengine.document import Document
from mongoengine.fields import StringField, IntField

from asyncmongoengine import connection
from asyncmongoengine.document import apply_patch

DBName = "main"

class User(Document):
    meta = {
        "index": [{"fields": ["sid"], "unique": True}]
    }
    sid = StringField()
    name = StringField()
    age = IntField()

class TestAsyncDocumentMethod(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        connection.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb")
        await connection.client.drop_database(DBName)
        connection.db = connection.client[DBName]
        apply_patch()

    async def test_unique_index(self):
        User.ensure_indexes()
        await User(sid="1", name="AA").save_async()