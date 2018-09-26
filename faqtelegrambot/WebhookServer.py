import cherrypy
import telebot

from .utility import exception_info


class WebhookServer(object):

    def __init__(self, bot):
        self.bot = bot

    @cherrypy.expose
    def index(self):
        try:
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            self.bot.process_new_updates([update])
        except Exception as ex:
            print(exception_info(ex))
        return ""
