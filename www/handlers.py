import asyncio

from www.coroweb import get
from www.model import User


@get("/hello/{arg}")
async def hello(request, arg):
    return {"hello": arg}

@get("/user/{id}")
async def hello(request, id):
    return await User.find(id)