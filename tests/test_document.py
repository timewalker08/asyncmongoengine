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

class Animal(Document):
    meta = {"allow_inheritance": True}

    type = StringField()

class Cat(Animal):
    pass

class Dog(Animal):
    pass

class TestAsyncDocumentMethod(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        connection.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb")
        connection.db = connection.client[DBName]
        apply_patch()

    async def test_save_async(self):
        user = User(name="Julius Caesar", age=56)
        user_saved = await user.save_async()
        self.assertIsNotNone(user_saved)
        self.assertTrue(isinstance(user_saved, User))

        dog = Dog(type="Dog")
        dog_saved = await dog.save_async()
        self.assertTrue(isinstance(dog_saved, Dog))

        cat = Cat(type="Cat")
        cat_saved = await cat.save_async()
        self.assertTrue(isinstance(cat_saved, Cat))

        animal = Animal(type="Animal")
        animal_saved = await animal.save_async()
        self.assertTrue(isinstance(animal_saved, Animal))
