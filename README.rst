FAQTelegramBot
==============

Frequently asked questions Telegram bot.


Features
--------

* Building dialogues with several questions and answers
* 3 types of user: Default, Moderator, Admin
* Moderator panel, to add, edit, delete, order questions and answers
* Admin panel, to manage rights


Screenshots
-----------

Soon

.. Ready questions on buttons:
.. image:: https://github.com/lonsofore/faqtelegrambot/blob/master/screenshots/1.png
    
.. Dialog example:
.. image:: https://github.com/lonsofore/faqtelegrambot/blob/master/screenshots/2.png
    
.. Mod menu:
.. image:: https://github.com/lonsofore/faqtelegrambot/blob/master/screenshots/3.png
    
.. Admin menu:
.. image:: https://github.com/lonsofore/faqtelegrambot/blob/master/screenshots/4.png


Installing
----------

Configure a virtual environment for the project:
.. code-block:: bash
    python3 -m venv bot
    cd bot
    source bin/activate

Download the repo and install it:
.. code-block:: bash
    git clone https://github.com/lonsofore/faqtelegrambot
    cd faqtelegrambot
    python3 setup.py install


Configure
---------

Before start prepare your config.yaml:
- The most important is token - you can register a new bot and get the token from from BotFather
- You can start with it, but if you want to get more stability, configure webhook


Start
-----

$ faqtelegrambot


To Do
-----

* MySQL compatibility
* Creating DB structure in code
* Starting with arguments via argparse (as an alternative to config.yaml file)
* Just a path to a file with proxies list in config


License
-------

Licensed under the Apache License, Version 2.0
