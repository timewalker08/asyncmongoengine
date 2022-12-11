from typing import Any, Optional

from mongoengine.base import get_document
from mongoengine.document import Document
from pymongo import ASCENDING, DESCENDING, IndexModel

from asyncmongoengine import connection


def create_indexes_async(cls):
    pass
