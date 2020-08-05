
import asyncio

import asyncmongoengine.fields as f
from asyncmongoengine.document import Document


class User(Document):
    name = f.StringField(db_field="n", required=True)
    age = f.IntField(db_field="a", required=True)


async def main():
    user = User(name="antony", age=10)

    print(user.name)
    print(user.age)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
