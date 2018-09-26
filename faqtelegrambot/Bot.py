import time
import logging

import telebot
from telebot import apihelper
import cherrypy
import asyncio

from faqtelegrambot import CONFIG
from .UserMessage import UserMessage
from .WebhookServer import WebhookServer
from .Proxy import Proxy
from .utility import is_url_available, exception_info


logger = logging.getLogger("bot")

API_URL = "http://api.telegram.org"


class Bot:

    def __init__(self, token, url=None, port=None, cert=None):
        self.token = token
        self.url = url
        self.port = port
        self.cert = cert

        self.is_active = False
        self.users = []  # type: [UserMessage]
        
        self.install_mode = self.check_users_count()        

        self.bot = telebot.TeleBot(self.token, threaded=False)
        
    def check_users_count(self):
        install_mode = True
        count = UserMessage.db_select_users_count()
        if count is not None and count > 0:
            install_mode = False
        return install_mode     

    def start(self):
        self.is_active = True
        while self.is_active:
            if CONFIG["proxy"]["use_always"] is True:  # should we use proxy always?
                self.update_proxy()
            else:  # if not - try to connect to telegram api first
                if not is_url_available(url=API_URL):
                    logger.info("No connection to {}. Trying to use proxy...".format(API_URL))
                    self.update_proxy()

            try:
                if self.url is None:
                    logger.info("Bot started (polling).")
                    self.bot.remove_webhook()

                    self.bot.polling(none_stop=True)
                    self.is_active = False

                else:
                    logger.info("Bot started (webhook).")
                    self.bot.remove_webhook()
                    if self.cert is None:
                        self.bot.set_webhook(url=self.url)
                    else:
                        self.bot.set_webhook(url=self.url, certificate=open(self.cert, "r"))

                    cherrypy.config.update({
                        "server.socket_host": "127.0.0.1",
                        "server.socket_port": self.port,
                        "engine.autoreload.on": False
                    })
                    cherrypy.quickstart(WebhookServer(self.bot), "/", {"/": {}})
                    self.is_active = False

            except BaseException as ex:
                # logger.error(ex)
                logger.info("Connection error.")
                time.sleep(5)

    def stop(self):
        pass

    @staticmethod
    def set_proxy(proxy: Proxy):
        apihelper.proxy = {proxy.proxy_type: proxy.url}

    def update_proxy(self):
        setted = False
        while not setted:
            proxy_list = CONFIG["proxy"]["list"]
            if proxy_list is not None and len(proxy_list) > 0:
                proxies = Proxy.parse_from_urls_list(proxy_list)
                proxy = Proxy.get_one_good_from_list(proxies)
                if proxy is not None:
                    setted = True
                    self.set_proxy(proxy)
                    logger.info("Setted proxy from list: {}".format(proxy))
                else:
                    logger.info("No good proxies in list")

            if not setted:
                logger.info("Searching for available proxies on the internet...")

                proxy = None
                try:
                    proxy = Proxy.find1(CONFIG["proxy"]["types"], CONFIG["proxy"]["countries"])  # type: Proxy
                except Exception as ex:
                    print(exception_info(ex))

                if proxy is not None:
                    setted = True
                    self.set_proxy(proxy)
                    logger.info("Setted proxy automatically: {}".format(proxy))
                else:
                    logger.info("No good proxies on the internet =(")

            if not setted:
                logger.info("Waiting...")
                time.sleep(CONFIG["proxy"]["wait"])

    def init_user(self, from_user):
        user = None
        for u in self.users:
            if u.id == from_user.id:
                return u
                
        if self.install_mode:
            level = UserMessage.get_max_level()
        else:
            level = UserMessage.get_default_level()

        user = UserMessage(
            user_id=from_user.id,
            first_name=from_user.first_name,
            last_name=from_user.last_name,
            username=from_user.username,
            language_code=from_user.language_code,
            level=level
        )
        user.init_user()
        self.users.append(user)
        return user

    def decorator_message(self, func):
        def wrapper(message):
            # init user
            message.user = self.init_user(message.from_user)  # type: UserMessage

            # to prevent flood
            if message.user.flood:
                logger.debug("{}: flood".format(message.user.id))
                return
            message.user.flood = True

            # execute
            func(message)

            # remove user's flood flag
            time.sleep(0.5)
            message.user.flood = False

        return wrapper

    def decorator_callback(self, func):
        def wrapper(call):
            # init user
            call.user = self.init_user(call.from_user)  # type: UserMessage

            # execute
            func(call)

        return wrapper
