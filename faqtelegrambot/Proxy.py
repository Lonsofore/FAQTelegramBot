import re

import proxy_list
import asyncio
from proxybroker import Broker

from faqtelegrambot import CONFIG
from .utility import is_url_available


CHECK_URL = CONFIG["proxy"]["check_url"]
TIMEOUT = CONFIG["proxy"]["timeout"]


class Proxy:

    def __init__(self, ip, port, proxy_type, login=None, password=None, country=None):
        self.ip = ip
        self.port = port
        self.proxy_type = proxy_type
        self.login = login
        self.password = password
        self.country = country

        self.url = self.get_url()

    def get_url(self):
        """socks5://login:password@ip:port"""
        if self.login is not None and self.password is not None:
            return "{}://{}:{}@{}:{}".format(self.proxy_type, self.login, self.password, self.ip, self.port)
        elif self.ip is not None and self.port is not None and self.proxy_type is not None:
            return "{}://{}:{}".format(self.proxy_type, self.ip, self.port)
        else:
            # return None
            return "{} {} {}".format(self.ip, self.port, self.proxy_type)

    def is_bad(self):
        return Proxy.is_bad_proxy(self)

    def __str__(self):
        return self.url

    @staticmethod
    def is_bad_proxy(proxy):
        return is_url_available(
            url=CHECK_URL,
            proxy=proxy,
            timeout=TIMEOUT
        )

    @staticmethod
    def get_good_from_list(proxies):
        result_list = list()
        for proxy in proxies:
            if not Proxy.is_bad_proxy(proxy):
                result_list.append(proxy)
        return result_list

    @staticmethod
    def get_one_good_from_list(proxies):
        for proxy in proxies:
            if not Proxy.is_bad_proxy(proxy):
                return proxy
        return None

    @staticmethod
    def find(proxy_types=None, countries=None):
        arr = Proxy.find_list(1, proxy_types=proxy_types, countries=countries)
        if len(arr) > 0:
            return arr[0]
        else:
            return None

    @staticmethod
    def find1(proxy_types=None, countries=None):
        arr = Proxy.find_list1(1, proxy_types=proxy_types, countries=countries)
        if len(arr) > 0:
            return arr[0]
        else:
            return None

    @staticmethod
    def find_list(count, proxy_types, countries=None):  # proxy_list
        proxy_list.update()

        proxies = []
        for proxy_type in proxy_types:
            selector = {}
            if countries is not None:
                selector["country"] = countries
            if proxy_types is not None:
                selector["type"] = proxy_type.lower()  # for some reason it needs only lower
            proxies += proxy_list.get(selector=selector, count=count)

        result = []
        for p in proxies:
            proxy = Proxy(ip=p['ip'], port=p['port'], proxy_type=p['type'], country=p['country'])
            if not proxy.is_bad():
                result.append(proxy)

        return result

    @staticmethod
    def find_list1(count, proxy_types, countries=None):  # proxybroker
        proxies_list = []

        map(lambda x: x.upper(), proxy_types)  # for some reason it needs only upper

        async def show(proxies):
            while True:
                proxy = await proxies.get()
                if proxy is None:
                    break

                for key in proxy.types:
                    p = Proxy(ip=proxy.host, port=proxy.port, proxy_type=key)
                    proxies_list.append(p)
                    if len(proxies_list) >= count:
                        break

                if len(proxies_list) >= count:
                    break

        proxies = asyncio.Queue()
        broker = Broker(proxies)
        if countries is None:
            tasks = asyncio.gather(broker.find(types=proxy_types, limit=count), show(proxies))
        else:
            tasks = asyncio.gather(broker.find(types=proxy_types, limit=count, countries=countries), show(proxies))

        # loop = asyncio.get_event_loop()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tasks)

        return proxies_list

    @staticmethod
    def parse_from_url(url):
        """socks5://login:password@ip:port"""

        pattern_login = "(\w+):\/\/(\w+):(.+)@(.*):(\d+)"
        pattern_nologin = "(\w+):\/\/(.*):(\d+)"

        result = re.match(pattern_login, url)
        if result is not None:
            proxy_type, login, password, ip, port = result.groups()
            return Proxy(ip, port, proxy_type, login, password)

        result = re.match(pattern_nologin, url)
        if result is not None:
            proxy_type, ip, port = result.groups()
            return Proxy(ip, port, proxy_type)

        return None

    @staticmethod
    def parse_from_urls_list(urls):
        proxies = []
        for url in urls:
            proxy = Proxy.parse_from_url(url)
            if proxy is not None:
                proxies.append(proxy)
        return proxies
