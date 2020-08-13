
import asyncio
from datetime import datetime
from decimal import Decimal

import asyncmongoengine.fields as f
from asyncmongoengine.connection import connect
from asyncmongoengine.document import Document, EmbeddedDocument

class Address(EmbeddedDocument):
    province = f.StringField(db_field="p", required=True)

class Books(EmbeddedDocument):
    name = f.StringField(db_field="n", required=True)

class User(Document):
    name = f.StringField(db_field="n", required=True)
    age = f.IntField(db_field="a", required=True)
    address = f.EmbeddedDocumentField(Address, db_field="ad")
    tags = f.ListField(f.StringField(), db_field="t", default=list)
    books = f.ListField(f.EmbeddedDocumentField(Books), db_field="b")
    
    x1 = f.LongField(db_field="x1", required=True)
    x2 = f.FloatField(db_field="x2", required=True)
    x3 = f.DecimalField(db_field="x3", required=True, force_string=True)
    x4 = f.BooleanField(db_field="x4", required=True)
    x5 = f.DateTimeField(db_field="x5", required=True)
    x6 = f.DateField(db_field="x6", required=True)



async def main():
    connect(host="mongo", port=27017)

    user = User(
        name="antony",
        age=10,
        address=Address(province="Shanghai"),
        books=[Books(name="Book1"), Books(name="Book2")],
        tags=["A", "B"],
        x1 = 122,
        x2 = 122.3,
        x3 = Decimal("5.21"),
        x4 = True,
        x5 = datetime.utcnow(),
        x6 = datetime.utcnow()
    )

    await user.save_async()
    print(user.name)
    print(user.age)

    #users = [User(name="name_{0}".format(x), age=x) for x in range(10)]
    #await asyncio.gather(*[u.save_async() for u in users])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
