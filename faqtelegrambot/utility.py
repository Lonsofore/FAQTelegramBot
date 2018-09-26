import inspect
import os
import sys
import gettext

import emoji
import requests
from ruamel import yaml


def loc(text, lang):
    gt = gettext.translation(
        domain=CONFIG["translate"]["domain"],
        localedir=CONFIG["translate"]["dir"],
        languages=[lang, "en"]
    )
    return gt.gettext(text)


def loc_emoji(text, lang, text_emoji):
    result = emoji.emojize(
        "{0} {1}".format(
            text_emoji,
            loc(text, lang)
        )
    )
    return result


def exception_info(ex):
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    return message


def enquote1(text):
    """Quotes input string with single-quote"""
    in_str = text.replace("'", r"\'")
    return "'%s'" % text


def enquote2(text):
    """Quotes input string with double-quote"""
    in_str = text.replace('"', r'\"')
    return '"%s"' % text


def is_url_available(url, proxy=None, timeout=None):
    if timeout is None:
        timeout = 5

    try:
        if proxy is None:
            r = requests.get(
                url=url,
                timeout=timeout
            )
        else:
            r = requests.get(
                url=url,
                proxies={proxy.proxy_type: proxy.url},
                timeout=timeout
            )
    except requests.RequestException as e:
        return True
    else:
        return False
        
def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)
    
def get_config(name):
    path = os.path.join(get_script_dir(),'config.yml')
    config = yaml.safe_load(open(path, "r"))
    return config
