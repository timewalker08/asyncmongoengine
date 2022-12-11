
import motor.motor_asyncio
from mongoengine import connect as mongoengine_connect

client = None
db = None

def connect(host, port=27017):
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(host, port)