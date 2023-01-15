import unittest

import motor.motor_asyncio
from mongoengine.connection import connect
from mongoengine.document import Document
from mongoengine.fields import IntField, StringField

from asyncmongoengine import connection
from asyncmongoengine.document import apply_patch

DBName = "main"

class User(Document):
    meta = {
        "indexes": [{"fields": ["sid"], "unique": True}]
    }
    sid = StringField()
    name = StringField()
    age = IntField()

class TestAsyncDocumentMethod(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        host = "mongodb"
        port = 27017
        username = "root"
        password = "password"
        connection.client = motor.motor_asyncio.AsyncIOMotorClient(host, port, username=username, password=password)
        await connection.client.drop_database(DBName)
        connection.db = connection.client[DBName]
        apply_patch()
        connect(host=host, port=port, db=DBName, username=username, password=password)

    async def test_unique_index(self):
        User.ensure_indexes()
        await User(sid="1", name="AA").save_async()
        await User(sid="1", name="AA").save_async()