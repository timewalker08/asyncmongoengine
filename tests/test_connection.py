import asyncio

from asyncmongoengine.connection import connect, get_db


async def main():
    connect("spider", "spider")

    db = get_db("spider")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
