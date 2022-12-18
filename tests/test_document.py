import unittest

import motor.motor_asyncio
from mongoengine.document import Document, EmbeddedDocument
from mongoengine import fields

from asyncmongoengine import connection
from asyncmongoengine.document import apply_patch

DBName = "main"


class User(Document):
    name = fields.StringField()
    gender = fields.StringField()
    age = fields.IntField()

class Animal(Document):
    meta = {"allow_inheritance": True}
    type = fields.StringField()

class Cat(Animal):
    pass

class Dog(Animal):
    pass

class Address(EmbeddedDocument):
    city = fields.StringField()

class WorkLocation(Document):
    name = fields.StringField()
    address = fields.EmbeddedDocumentField(Address)


class TestAsyncDocumentMethod(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        connection.client = motor.motor_asyncio.AsyncIOMotorClient("mongodb", 27017, username="root", password="password")
        await connection.client.drop_database(DBName)
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

    async def test_embededdocument(self):
        location = WorkLocation(name="Office", address=Address(city="Shanghai"))
        location_saved = await location.save_async()
        self.assertIsNotNone(location_saved)
        self.assertTrue(isinstance(location_saved, WorkLocation))
        self.assertTrue(isinstance(location_saved.address, Address))

    async def test_find(self):
        user1 = User(name="Julius Caesar", age=56)
        user1 = await user1.save_async()

        user2 = User(name="Mark Antony", age=48)
        user2 = await user2.save_async()

        users = set([user1, user2])

        async for user in User.find({}):
            self.assertIsNotNone(user)

        async for user in User.find_async({}):
            self.assertIsNotNone(user)
            self.assertTrue(user in users)

        users = [user async for user in User.find_async({"name": "Julius Caesar"})]
        self.assertEqual(len(users), 1)

        users = [user async for user in User.find_async({"name": {"$in": ["Julius Caesar", "Mark Antony"]}})]
        self.assertEqual(len(users), 2)

    async def test_find_one_and_update(self):
        user = User(name="Julius Caesar", age=56)
        await user.save_async()

        user = await User.find_one_and_update_async(filter={"name": "Julius Caesar"}, update={"$set": {"age": 60}})
        self.assertEqual(user.name, "Julius Caesar")
        self.assertEqual(user.age, 56)

        user = await User.find_one_async({"name": "Julius Caesar"})
        self.assertEqual(user.age, 60)

        user = await User.find_one_async({"name": "No Body"})
        self.assertIsNone(user)
