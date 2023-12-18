import asyncio
import inspect
import json
import logging
import os

from aiohttp import web
from aiohttp.web_middlewares import middleware

from www import orm
from www.coroweb import RequestHandler


def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    # if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
    #     fn = asyncio.coroutine(fn)
    logging.info(
        'add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))

def add_static(app):
    # /www/static
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    # Add a router and a handler for returning static files
    # Development only, in production, use web servers like nginx or apache
    app.router.add_static('/static/', path)
    logging.info('Add static %s => %s' % ('/static/', path))


def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n + 1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)


# @middleware
# async def logger_factory(request, handler):
#     # 记录日志:
#     logging.info('Request: %s %s' % (request.method, request.path))
#     resp = await handler(request)
#     return resp


@middleware
async def response_factory(request, handler):
    # 结果:
    r = await handler(request)
    if isinstance(r, web.StreamResponse):
        return r
    if isinstance(r, bytes):
        resp = web.Response(body=r)
        resp.content_type = 'application/octet-stream'
        return resp
    if isinstance(r, str):
        resp = web.Response(body=r.encode('utf-8'))
        resp.content_type = 'text/html;charset=utf-8'
        return resp
    if isinstance(r, dict):
        resp = web.Response(body=json.dumps(r))
        resp.content_type = 'application/json'
        return resp


loop = asyncio.get_event_loop()
app = web.Application(middlewares=[
    response_factory
])
add_routes(app, 'handlers')
async def init_db():
    mysql_dict = {
        "host": "47.97.65.248",
        "port": 30006,
        "user": "chenfeilong",
        "password": "0ReCmLrPbhW3RBn0",
        "db": "ad"
    }
    await orm.create_pool(
        mysql_dict
    )

# app.on_startup.append(init_db)
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    web.run_app(app, host='127.0.0.1', port=8000)
