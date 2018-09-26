import os

from .utility import get_config, get_script_dir

__version__ = '1.0'
CONFIG_NAME = 'config.yml'
CONFIG = get_config(CONFIG_NAME)
DB_PATH = os.path.join(get_script_dir(), CONFIG['db_name'])
