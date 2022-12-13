
import motor.motor_asyncio
from mongoengine import connect as mongoengine_connect

client = None
db = None

def connect(host, port, username, password, auth_db):
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(host, port, username=username, password=password, authSource=auth_db)