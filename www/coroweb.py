import functools
import inspect
import logging
from urllib import parse

from aiohttp import web


def get(path):
    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper

    return decorator


def post(path):
    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper

    return decorator


def delete(path):
    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'DELETE'
        wrapper.__route__ = path
        return wrapper

    return decorator


def put(path):
    '''
    Define decorator @get('/path')
    '''

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)

        wrapper.__method__ = 'PUT'
        wrapper.__route__ = path
        return wrapper

    return decorator

class RequestHandler(object):

    def __init__(self, app, fn):
        self._app = app
        self._func = fn

    def get_required_kwargs(fn):
        """
        获取函数命名关键字参数，且非默认参数

        :param fn: function
        :return:
        """
        args = []
        # 获取函数 fn 的参数，ordered mapping
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            # * 或者 *args 后面的参数，且没有默认值
            if param.kind == param.KEYWORD_ONLY and param.default is param.empty:
                args.append(name)
        return tuple(args)

    def get_named_kwargs(fn):
        """
        获取函数命名关键字参数

        :param fn: function
        :return:
        """
        args = []
        # 获取函数 fn 的参数，ordered mapping
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            # * 或者 *args 后面的参数
            if param.kind == param.KEYWORD_ONLY:
                args.append(name)
        return tuple(args)

    def has_named_kwarg(fn):
        """
        判断是否有命名关键字参数

        :param fn: function
        :return:
        """
        # 获取函数 fn 的参数，ordered mapping
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            # * 或者 *args 后面的参数
            if param.kind == param.KEYWORD_ONLY:
                return True


    def has_var_kwarg(fn):
        """
        判断是否有关键字参数

        :param fn: function
        :return:
        """
        # 获取函数 fn 的参数，ordered mapping
        params = inspect.signature(fn).parameters
        for name, param in params.items():
            # **args 后面的参数
            if param.kind == param.VAR_KEYWORD:
                return True

    def has_request_arg(fn):
        """
        判断是否有请求参数

        :param fn: function
        :return:
        """
        # 获取函数 fn 的签名
        sig = inspect.signature(fn)
        # 获取函数 fn 的参数，ordered mapping
        params = sig.parameters
        found = False
        for name, param in params.items():
            if name == 'request':
                found = True
                continue
            if found and (param.kind is not param.VAR_POSITIONAL and
                          param.kind is not param.KEYWORD_ONLY and
                          param.kind is not param.VAR_KEYWORD):
                # fn(*args, **kwargs)，fn 为 fn.__name__，(*args, **kwargs) 为 sig
                raise ValueError(
                    'Request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
        return found

    async def __call__(self, request):

        kwargs = None
        if self.has_var_kwarg() or self.has_named_kwarg() or self.get_required_kwargs():
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest(text='Missing Content-Type.')
                ct = request.content_type.lower()
                # JSON 数据格式
                if ct.startswith('application/json'):
                    # Read request body decoded as json
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest(text='JSON body must be dict object.')
                    kwargs = params
                # form 表单数据被编码为 key/value 格式发送到服务器（表单默认的提交数据的格式）
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    # Read POST parameters from request body
                    params = await request.post()
                    kwargs = dict(**params)
                else:
                    return web.HTTPBadRequest(text='Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                # The query string in the URL, e.g., id=10
                qs = request.query_string
                if qs:
                    kwargs = dict()
                    # {'id': ['10']}
                    for k, v in parse.parse_qs(qs, True).items():
                        kwargs[k] = v[0]
        if kwargs is None:
            kwargs = dict(**request.match_info)
        else:
            if not self.__has_var_kwarg and self.__named_kwargs:
                # Remove all unnamed kwargs
                copy = dict()
                for name in self.__named_kwargs:
                    if name in kwargs:
                        copy[name] = kwargs[name]
                kwargs = copy
            # Check named kwargs
            for k, v in request.match_info.items():
                if k in kwargs:
                    logging.warning('Duplicate arg name in named kwargs and kwargs: %s' % k)
                kwargs[k] = v
        if self.has_request_arg():
            kwargs['request'] = request
        # Check required kwargs
        if self.get_required_kwargs():
            for name in self.get_required_kwargs():
                if name not in kwargs:
                    return web.HTTPBadRequest(text='Missing argument: %s' % name)
        logging.info('Call with kwargs: %s' % str(kwargs))
        r = await self._func(**kwargs)
        return r

