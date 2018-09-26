from io import open
from setuptools import setup, find_packages
from os.path import join, dirname

from faqtelegrambot import __version__


with open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()
    
with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read()


setup(
    # metadata
    name='faqtelegrambot',
    version=__version__,
    url='https://github.com/lonsofore/faqtelegrambot/',
    author='Lonsofore',
    author_email='lonsofore@yandex.ru',
    license='Apache 2.0',
    description='Frequently asked questions Telegram bot.',
    long_description=readme,
    keywords='telegram faq bot',

    # options
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'faqtelegrambot = faqtelegrambot.start:start',
        ],
    },
)
