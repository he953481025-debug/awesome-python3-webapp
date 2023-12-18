import asyncio

import orm
from model import User, Blog, Comment

def test():
    mysql_dict = {
        "host": "47.97.65.248",
        "port": 30006,
        "user": "chenfeilong",
        "password": "0ReCmLrPbhW3RBn0",
        "db": "ad"
    }
    loop = asyncio.get_event_loop()
    loop.run_until_complete(orm.create_pool(mysql_dict))
    # user = User(id=123, name='Michael')
    # users = loop.run_until_complete(User.findAll())
    # u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank', admin=True)
    print(loop.run_until_complete(User.find("123")))


if __name__ == '__main__':
    test()