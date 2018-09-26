import logging
import sys
import os

import cherrypy

from faqtelegrambot import CONFIG
from .utility import get_script_dir
from .BotMessage import BotMessage
from .WebhookRouter import WebhookRouter
from .cert import create as create_cert


format_full = '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
format_short = '%(asctime)s %(levelname)s: "%(message)s"'
formatter_short = logging.Formatter(format_short)
formatter_full = logging.Formatter(format_full)

logging.basicConfig(
    level=logging.WARNING,
    format=format_full,
    datefmt='%m-%d %H:%M',
    filename=os.path.join(get_script_dir(), CONFIG['log_name']),
    filemode='w'
)

logger = logging.getLogger("bot")

handler_console = logging.StreamHandler(sys.stdout)
handler_console.setFormatter(formatter_short)
logger.addHandler(handler_console)
logger.setLevel(logging.DEBUG)


def start():
	if CONFIG["webhook"]["enabled"] is False:  # polling
		bot = BotMessage(
			token=CONFIG["token"]
		)
		bot.start()

	else:  # webhook
		# settings
		url = "https://{}:{}/{}/".format(
			CONFIG["webhook"]["domain"],
			CONFIG["webhook"]["port_out"],
			CONFIG["webhook"]["link"]
		)

		if CONFIG["webhook"]["ssl"]["enabled"]:
			if CONFIG["webhook"]["ssl"]["cert"] == "":
				cert_name = "bot"
				create_cert(name=cert_name)
				cert = "{}.crt".format(cert_name)
			else:
				cert = CONFIG["webhook"]["ssl"]["cert"]

			# bot
			bot = BotMessage(
				token=CONFIG["token"],
				url=url,
				port=CONFIG["webhook"]["port_in"],
				cert=cert
			)
			bot.start()
		else:
			bot = BotMessage(
				token=CONFIG["token"],
				url=url,
				port=CONFIG["webhook"]["port_in"]
			)
			bot.start()

		# router
		if CONFIG["webhook"]["router"]["enabled"] is True:
			cherrypy.config.update({
				"server.socket_host": CONFIG["webhook"]["router"]["host"],
				"server.socket_port": CONFIG["webhook"]["port_out"],
				"server.ssl_module": "builtin",
				"server.ssl_certificate": CONFIG["webhook"]["ssl"]["cert"],
				"server.ssl_private_key": CONFIG["webhook"]["ssl"]["priv"],
				"engine.autoreload.on": False
			})
			cherrypy.quickstart(WebhookRouter(), '/', {'/': {}})


if __name__ == "__main__":
    start()
