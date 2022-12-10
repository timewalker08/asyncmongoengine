import unittest

import motor.motor_asyncio
from mongoengine.document import Document
from mongoengine.fields import StringField, IntField

from asyncmongoengine import connection
from asyncmongoengine.document import apply_patch

DBName = "main"


class User(Document):
    name = StringField()
    age = IntField()

class TestAsyncDocumentMethod(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        connection.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb")
        connection.db = connection.client[DBName]
        apply_patch()

    async def test_save_async(self):
        user = User(name="Julius Caesar", age=56)
        await user.save_async()
