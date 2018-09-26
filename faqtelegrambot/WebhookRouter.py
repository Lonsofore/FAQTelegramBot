import cherrypy
import requests

from faqtelegrambot import CONFIG


class WebhookRouter(object):

    @cherrypy.expose
    def AAAA(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            requests.post(
                "http://127.0.0.1:{}".format(CONFIG["webhook"]["port_in"]),
                data=json_string
            )
            return ""
        else:
            raise cherrypy.HTTPError(403)
