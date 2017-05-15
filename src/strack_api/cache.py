# coding: utf-8
# copyright: Copyright (c) 2016 Strack

__author__ = 'NJB'

import abc
import anydbm
import re
import contextlib
import collections
import pickle
import inspect
import copy
import functools


class Cache(object):
    __metaclass__ = abc.ABCMeta


    @abc.abstractmethod
    def get(self, key):
        '''
        :param key:
        :return: value of the key
        '''

    @abc.abstractmethod
    def set(self, key, value):
        '''
        设置cache的键值对
        :param key: 键名
        :param value: 值
        :return: 无
        '''

    @abc.abstractmethod
    def remove(self, key):
        '''
        删除某个键值对
        :param key: 键名
        :return:返回 键的值
        '''

    def keys(self):
        '''
        返回所有的键名
        :return:列表，键名
        '''

        raise NotImplementedError()

    def clear(self, pattern=None):
        '''
        按照pattern 清理cache
        :param pattern: 正则表达式，如果为none，则清理所有键值
        :return:
        '''
        if pattern is not None:
            pattern = re.compile(pattern)

        for key in self.keys():
            if pattern is not None:
                if not pattern.search(key):
                    continue
            try:
                self.remove(key)
            except KeyError:
                pass


class ProxyCache(Cache):
    '''
    代理另外一个cache
    '''

    def __init__(self, proxied):
        '''
        初始化
        :param proxied: 被代理的cache
        :return:无
        '''
        self.proxied = proxied
        super(ProxyCache, self).__init__()

    def get(self, key):
        '''
        获取键值
        :param key:键名
        :return:键值
        '''
        return self.proxied.get(key)

    def set(self, key, value):
        '''
        设置键值
        :param key:键名
        :param value: 值
        :return:无
        '''
        self.proxied.set(key, value)

    def remove(self, key):
        '''
        删除某个键值
        :param key:键名
        :return:值
        '''
        return self.proxied.remove(key)

    def keys(self):
        '''
        返回当前代理的键名列表
        :return:键名列表
        '''
        return self.proxied.keys()


class CascadeCache(Cache):
    '''
    层级cache
    '''
    #Todo 根据实际使用决定是否删除这个类
    def __init__(self, caches):
        '''
        使用多个cache初始化
        :param caches: 多个cache，可能是列表
        :return:无
        '''
        super(LayeredCache, self).__init__()
        self.caches = caches

    def get(self, key):
        '''
        如果没找到对应的key，返回‘KeyError’
        :param key: 键名
        :return:键值
        '''

        target_caches = []
        value = None

        for cache in self.caches:
            try:
                value = cache.get(key)
            except KeyError:
                target_caches.append(cache)
                continue
            else:
                break

        if value is None:
            raise KeyError(key)

        # 在高层的cache中设置对应的键值
        for cache in target_caches:
            cache.set(key, value)

        return value

    def set(self, key, value):
        '''
        设置键值，循环查找
        :param key: 键
        :param value: 值
        :return:
        '''
        for cache in self.caches:
            cache.set(key, value)

    def remove(self, key):
        '''
        删除键值对
        :param key: 键
        :return:无
        '''
        for cache in self.caches:
            cache.remove(key)

    def keys(self):
        '''
        返回键名列表
        :return:
        '''
        keys = []
        for cache in self.caches:
            keys.extend(cache.keys())

        # 去重
        return list(set(keys))

class MemoryCache(Cache):
    '''
    内存cache
    '''
    def __init__(self):
        self._cache = {}
        super(MemoryCache, self).__init__()

    def get(self, key):
        return self._cache[key]

    def set(self, key, value):
        self._cache[key] = value

    def remove(self, key):
        del self._cache[key]

    def keys(self):
        return self._cache.keys()


class FileCache(Cache):
    '''
    基于文件的cache
    '''
    def __init__(self, path):
        self.path = path

        # 只需要记录文件路径
        cache = anydbm.open(self.path, 'c')
        cache.close()

        super(FileCache, self).__init__()

    @contextlib.contextmanager
    def _database(self):
        cache = anydbm.open(self.path, 'w')
        try:
            yield cache
        finally:
            cache.close()

    def get(self, key):
        with self._database() as cache:
            return cache[key]

    def set(self, key, value):
        with self._database() as cache:
            cache[key] = value

    def remove(self, key):
        with self._database as cache:
            del cache[key]

    def keys(self):
        with self._database() as cache:
            return cache.keys()
        

class SerialisedCache(ProxyCache):
    '''
    被代理的cache存放序列化的数据
    '''
    def __init__(self, proxied, encode=None, decode=None):
        self.encode = encode
        self.decode = decode
        super(SerialisedCache, self).__init__(proxied)
        
    def get(self, key):
        value = super(SerialisedCache, self).get(key)
        if self.encode:
            value = self.decode(value)
        
        return value
    
    def set(self, key, value):
        if self.encode:
            value = self.encode(value)
        super(SerialisedCache, self).set(key, value)


class KeyMaker(object):
    '''
    生成唯一的key,序列化时用
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(KeyMaker, self).__init__()
        self.item_separator = ''

    def key(self, *items):
        keys = []
        for item in items:
            keys.append(self._key(item))

        return self.item_separator.join(keys)

    @abc.abstractmethod
    def _key(self, obj):
        pass


class StringKeyMaker(KeyMaker):
    def _key(self, obj):
        return str(obj)


class ObjectKeyMaker(KeyMaker):
    def __init__(self):
        super(ObjectKeyMaker, self).__init__()
        self.item_separator = '\0'
        self.mapping_identifier = '\1'
        self.mapping_pair_separator = '\2'
        self.iterable_identifier = '\3'
        self.name_identifier = '\4'

    def _key(self, item):
        # todo 修改完善
        if isinstance(item, collections.Iterable):
            if isinstance(item, basestring):
                return pickle.dumps(item, pickle.HIGHEST_PROTOCOL)

            if isinstance(item, collections.Mapping):
                contents = self.item_separator.join([
                    (
                        self._key(key) +
                        self.mapping_pair_separator +
                        self._key(value)
                    )
                    for key, value in sorted(item.items())
                ])
                return (
                    self.mapping_identifier +
                    contents +
                    self.mapping_identifier
                )
            else:
                contents = self.item_separator.join([
                    self._key(item) for item in item
                ])
                return (
                    self.iterable_identifier +
                    contents +
                    self.iterable_identifier
                )
        elif inspect.ismethod(item):
            return ''.join((
                self.name_identifier,
                item.__name__,
                self.item_separator,
                item.__module__
            ))

        elif inspect.isbuiltin(item):
            return self.name_identifier + item.__name__

        else:
            return pickle.dumps(item, pickle.HIGHEST_PROTOCOL)


class Memoiser(object):
    def __init__(self, cache=None, key_maker=None, return_copies=True):
        self.cache = cache
        if self.cache is None:
            self.cache = MemoryCache()

        self.key_maker = key_maker
        if self.key_maker is None:
            self.key_maker = ObjectKeyMaker()

        self.return_copies = return_copies
        super(Memoiser, self).__init__()

    def call(self, function, args=None, kw=None):
        if args is None:
            args = ()

        if kw is None:
            kw = {}

        arguments = inspect.getcallargs(function, *args, **kw)

        key = self.key_maker.key(function, arguments)
        try:
            value = self.cache.get(key)
        except KeyError:
            value = function(*args, **kw)
            self.cache.set(key, value)

        if self.return_copies:
            value = copy.deepcopy(value)

        return value


def memoise_decorator(memoiser):
    def outer(function):

        @functools.wraps(function)
        def inner(*args, **kw):
            return memoiser.call(function, args, kw)
        return inner

    return outer

memoiser = Memoiser()

memoise = memoise_decorator(memoiser)















