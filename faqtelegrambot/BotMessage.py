import logging

from telebot import types
from telebot import apihelper
import emoji

from .utility import loc, loc_emoji
from .Bot import Bot
from .UserMessage import UserMessage
from .Message import MessageUser
from .Message import MessageBot


logger = logging.getLogger('bot')

EMOJI_ADMIN = ":hammer:"
EMOJI_MANAGE = ":wrench:"
EMOJI_WRONG = ":no_entry:"
EMOJI_NOTHING = ":question_mark:"
EMOJI_YES = ":heavy_check_mark:"
EMOJI_NO = ":heavy_multiplication_x:"
EMOJI_BACK = ":reverse_button:"
EMOJI_START = ":fast_reverse_button:"
EMOJI_UP = ":upwards_button:"
EMOJI_DOWN = ":downwards_button:"


class BotMessage(Bot):

    def __init__(self, token, url=None, port=None, cert=None):
        super().__init__(token, url, port, cert)
        self.init_handlers()

    def init_handlers(self):
        # simple messages
        @self.bot.message_handler(func=lambda message: True)
        @self.decorator_message
        def process_step(message):
            try:
                arr = message.text.split()

                if arr[0] == "/start":
                    self.process_message(message)

                elif arr[0] == "/manage" or arr[0] == "/edit":
                    if message.user.level > 0:
                        if message.user.mode > 0 \
                                or len(arr) > 1 and arr[1] == "exit":
                            message.user.change_mode(0)
                            message.user.reset_message_type()
                            self.repeat_last_message(message.user)
                        else:
                            message.user.change_mode(1)
                            self.repeat_last_message(message.user)

                elif arr[0] == "/admin":
                    if message.user.level > 1:
                        if message.user.mode > 0 \
                                or len(arr) > 1 and arr[1] == "exit":
                            message.user.change_mode(0)
                            message.user.reset_message_type()
                            self.repeat_last_message(message.user)
                        else:
                            message.user.change_mode(2)
                            self.message_admin(message.user)

                else:
                    if message.user.is_default_message_type():
                        self.process_message(message)
                    else:
                        arr = message.user.get_message_type().split()
                        if arr[0] == "manage":
                            self.process_manage(message)
                        elif arr[0] == "admin":
                            self.process_admin(message)

            except apihelper.ApiException as ex:
                logger.error("ApiException: {}".format(ex.args[0]))

        # inline callback
        @self.bot.callback_query_handler(func=lambda call: True)
        @self.decorator_callback
        def callback_inline(call):
            arr = call.data.split()
            if arr[0] == "manage":
                self.callback_manage(call)
            elif arr[0] == "admin":
                self.callback_admin(call)

    def process_message(self, message):
        message_bot = None
        message_user = None

        # check for a movement button
        if message.text == loc_emoji("Return to start", message.user.language_ui, EMOJI_START) \
                or message.text == "/start":
            message_bot = MessageBot.get_first()
            if message_bot is None:
                logger.debug("No first message. Inserted")
                message_bot = MessageBot.db_insert_message(MessageBot.empty(), None)
        elif message.text == loc_emoji("Back", message.user.language_ui, EMOJI_BACK):
            try:
                message_bot = message.user.message_bot \
                    .get_message_from() \
                    .get_message_from()
                message_user = message_bot.get_message_from()
            except AttributeError:
                pass
        else:
            message_user = self.init_message_user(message.user, message.text)
            if message_user is not None:
                message_bot = message_user.get_message()

        self.send_message_bot(user=message.user, message_bot=message_bot, message_user=message_user)

    def send_message_bot_first(self, user):
        message_bot = MessageBot.get_first()
        self.send_message_bot(user=user, message_bot=message_bot)

    def send_message_bot(self, user, message_bot=None, message_user=None):
        if message_bot is None:
            self.bot.send_message(
                user.id,
                loc_emoji("Error. Lets try from start again.", user.language_ui, EMOJI_WRONG)
            )
            logger.debug("Error: no message found")
            self.send_message_bot_first(user)
            return 1

        # save history
        user.save_history_message_bot(message_bot)  # new history line here
        if message_user is not None:
            user.save_history_message_user(message_user)

        # log to console
        if message_user is not None:
            logger.debug("{0}: {1} - {2}".format(user.id, message_user.id, message_bot.id))
        else:
            logger.debug("{0}: {1} - {2}".format(user.id, "none", message_bot.id))

        text = BotMessage.get_message_bot_text(user.language_ui, message_bot)
        messages_user = message_bot.get_messages()
        if messages_user is not None or user.mode > 0:
            markup = BotMessage.get_markup(
                language_ui=user.language_ui,
                message_bot=message_bot,
                messages_user=messages_user
            )

            user.message_bot = message_bot
            self.bot.send_message(user.id, text, reply_markup=markup)
        else:
            # user.message_bot = message_bot
            self.bot.send_message(user.id, text)

        if user.mode > 0:
            self.message_manage(user)

        return 0

    @staticmethod
    def get_message_bot_text(language_ui, message_bot):  # check for the empty message
        if message_bot.is_empty_text():
            text = loc_emoji(
                "No information for your request at this moment.",
                language_ui,
                EMOJI_NOTHING
            )
        else:
            text = message_bot.text
        return text

    @staticmethod
    def get_markup(language_ui, message_bot, messages_user):
        if message_bot.is_first():
            markup = BotMessage.get_markup_first(messages_user)
        else:
            markup = BotMessage.get_markup_not_first(messages_user, language_ui)
        return markup

    @staticmethod
    def get_markup_not_first(messages, language_ui):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # add messages buttons
        if messages is not None:
            for message in messages:
                markup.add(types.KeyboardButton(message.get_text()))

        # add movement buttons
        markup.add(
            types.KeyboardButton(
                loc_emoji("Back", language_ui, EMOJI_BACK)
            ),
            types.KeyboardButton(
                loc_emoji("Return to start", language_ui, EMOJI_START)
            )
        )

        return markup

    @staticmethod
    def get_markup_first(messages):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # add messages buttons
        if messages is not None:
            for message in messages:
                markup.add(types.KeyboardButton(message.get_text()))

        return markup

    @staticmethod
    def init_message_user(user: UserMessage, text):
        message_user = None

        # try to get it from the old message
        last = user.get_last_message_bot()
        if last is not None:
            messages = last.get_messages()
            if messages is not None:
                for message in messages:
                    if message.get_text() == text:
                        message_user = message
                        break

        # try to get it from the text
        if message_user is None:
            arr = MessageUser.db_select_messages_by_text(text)
            if arr is not None:
                message_user = arr[0]  # TODO: [0] is a bug, in fact

        return message_user

    def repeat_last_message(self, user: UserMessage):
        last_bot = user.get_last_message_bot()
        last_user = last_bot.get_message_from()
        if last_bot is not None:
            self.send_message_bot(user=user, message_bot=last_bot, message_user=last_user)
        else:
            logger.debug("No last answer")

    # MANAGE PART STARTS HERE
    def message_manage(self, user: UserMessage):
        if user.level > 0 and user.mode > 0:
            self.bot.send_message(
                user.id,
                loc_emoji("Manage mode", user.language_ui, EMOJI_MANAGE),
                reply_markup=self.get_markup_manage(user)
            )

    def callback_manage(self, call):
        if call.user.level > 0 and call.message:
            arr = call.data.split()
            if len(arr) > 1:
                if arr[1] == "edit_message_bot":
                    call.user.set_message_type("manage edit_message_bot")
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("Enter new bot message.", call.user.language_ui, EMOJI_MANAGE),
                        reply_markup=self.get_markup_cancel(call.user.language_ui, "manage cancel")
                    )

                elif arr[1] == "add_message_user":
                    call.user.set_message_type("manage add_message_user")
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("Enter new answer.", call.user.language_ui, EMOJI_MANAGE),
                        reply_markup=self.get_markup_cancel(call.user.language_ui, "manage cancel")
                    )

                elif arr[1] == "edit_message_user":
                    call.user.set_message_type("manage edit_message_user select")
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("Select answer to edit.", call.user.language_ui, EMOJI_MANAGE),
                        reply_markup=self.get_markup_cancel(call.user.language_ui, "manage cancel")
                    )

                elif arr[1] == "move_message_user":
                    if len(arr) > 2:
                        if arr[2] == "up":
                            if call.user.is_set_manage_message():
                                answer = call.user.get_manage_message()
                                res = answer.order_up()
                                if res == 0:
                                    messages_user = call.user.message_bot.get_messages()
                                    if messages_user is not None:
                                        markup = BotMessage.get_markup(
                                            language_ui=call.user.language_ui,
                                            message_bot=call.user.message_bot,
                                            messages_user=messages_user
                                        )

                                        # need to send message cause we need to update user messages
                                        self.bot.send_message(
                                            call.user.id,
                                            text=loc_emoji(
                                                "Order changed",
                                                call.user.language_ui,
                                                EMOJI_MANAGE
                                            ),
                                            reply_markup=markup
                                        )

                        elif arr[2] == "down":
                            if call.user.is_set_manage_message():
                                answer = call.user.get_manage_message()
                                res = answer.order_down()
                                if res == 0:
                                    messages_user = call.user.message_bot.get_messages()
                                    if messages_user is not None:
                                        markup = BotMessage.get_markup(
                                            language_ui=call.user.language_ui,
                                            message_bot=call.user.message_bot,
                                            messages_user=messages_user
                                        )

                                        # need to send message cause we need to update user messages
                                        self.bot.send_message(
                                            call.user.id,
                                            text=loc_emoji(
                                                "Order changed",
                                                call.user.language_ui,
                                                EMOJI_MANAGE
                                            ),
                                            reply_markup=markup
                                        )

                        elif arr[2] == "save":
                            self.bot.edit_message_text(
                                chat_id=call.message.chat.id,
                                message_id=call.message.message_id,
                                text="_",
                            )

                            call.user.reset_manage_message()
                            call.user.reset_message_type()
                            self.repeat_last_message(call.user)
                    else:
                        call.user.set_message_type("manage move_message_user select")
                        self.bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=loc_emoji("Select answer to move.", call.user.language_ui, EMOJI_MANAGE),
                            reply_markup=self.get_markup_cancel(call.user.language_ui, "manage cancel")
                        )

                elif arr[1] == "delete_message_user":
                    if len(arr) > 2:
                        if arr[2] == "yes":
                            if self.process_delete_message_user_confirm(call.user) == 0:
                                self.bot.edit_message_text(
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text=loc_emoji("Answer deleted", call.user.language_ui, EMOJI_MANAGE),
                                )
                            call.user.reset_message_type()
                            self.repeat_last_message(call.user)
                    else:
                        call.user.set_message_type("manage delete_message_user select")
                        self.bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=loc_emoji("Select answer to delete.", call.user.language_ui, EMOJI_MANAGE),
                            reply_markup=self.get_markup_cancel(call.user.language_ui, "manage cancel")
                        )

                elif arr[1] == "cancel":
                    call.user.reset_manage_message()
                    call.user.reset_message_type()
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("Manage mode", call.user.language_ui, EMOJI_MANAGE),
                        reply_markup=self.get_markup_manage(call.user)
                    )

                elif arr[1] == "exit":
                    call.user.change_mode(0)
                    call.user.reset_manage_message()
                    call.user.reset_message_type()
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("You exited manage mode.", call.user.language_ui, EMOJI_MANAGE)
                    )
                    self.repeat_last_message(call.user)

    def process_manage(self, message):
        arr = message.user.get_message_type().split()
        if arr[1] == "edit_message_bot":
            last = message.user.get_last_message_bot()
            if last is not None:
                last.set_text(message.text)
                self.bot.send_message(
                    message.user.id,
                    loc_emoji("Question edited", message.user.language_ui, EMOJI_MANAGE)
                )
            message.user.reset_message_type()

        elif arr[1] == "add_message_user":
            last = message.user.get_last_message_bot()
            if last is not None:
                last.add_message_user(message.text)
                self.bot.send_message(
                    message.user.id,
                    loc_emoji("Added new answer", message.user.language_ui, EMOJI_MANAGE)
                )
            message.user.reset_message_type()

        elif arr[1] == "edit_message_user":
            if len(arr) > 2:
                if arr[2] == "select":
                    message_user = self.init_message_user(message.user, message.text)
                    if message_user is None:
                        self.bot.send_message(
                            message.user.id,
                            loc_emoji("Error. Unknown variant.", message.user.language_ui, EMOJI_MANAGE)
                        )
                        # message.user.reset_message_type()
                    else:
                        message.user.set_manage_message(message_user)
                        message.user.set_message_type("manage edit_message_user edit")
                        self.bot.send_message(
                            message.user.id,
                            emoji.emojize(
                                "{0} {1}: {2}\r\n{3}".format(
                                    EMOJI_MANAGE,
                                    loc("You choosed", message.user.language_ui),
                                    message_user.text,
                                    loc("Now send me a new answer.", message.user.language_ui)
                                ),
                            ),
                            reply_markup=self.get_markup_cancel(message.user.language_ui, "manage cancel")
                        )

                elif arr[2] == "edit":
                    if message.user.is_set_manage_message():
                        message_old = message.user.get_manage_message()
                        message_old.set_text(message.text)
                        self.bot.send_message(
                            message.user.id,
                            loc_emoji("Answer edited", message.user.language_ui, EMOJI_MANAGE)
                        )
                    message.user.reset_message_type()

        elif arr[1] == "delete_message_user":
            if len(arr) > 2:
                if arr[2] == "select":
                    message_user = self.init_message_user(message.user, message.text)
                    if message_user is None:
                        self.bot.send_message(
                            message.user.id,
                            loc_emoji("Error. Unknown variant.", message.user.language_ui, EMOJI_WRONG)
                        )
                        # message.user.reset_message_type()
                    else:
                        message.user.set_manage_message(message_user)
                        message.user.set_message_type("manage delete_message_user confirm")
                        self.bot.send_message(
                            message.user.id,
                            emoji.emojize(
                                "{0} {1}: {2}\r\n{3}".format(
                                    EMOJI_MANAGE,
                                    loc("You choosed", message.user.language_ui),
                                    message_user.text,
                                    loc("Do you really want to delete this answer?", message.user.language_ui)
                                )
                            ),
                            reply_markup=self.get_markup_yes_no(
                                message.user.language_ui,
                                "manage delete_message_user yes",
                                "manage cancel"
                            )
                        )

        elif arr[1] == "move_message_user":
            if len(arr) > 2:
                if arr[2] == "select":
                    message_user = self.init_message_user(message.user, message.text)
                    if message_user is None:
                        self.bot.send_message(
                            message.user.id,
                            loc_emoji("Error. Unknown variant.", message.user.language_ui, EMOJI_MANAGE)
                        )
                        # message.user.reset_message_type()
                    else:
                        message.user.set_manage_message(message_user)
                        message.user.set_message_type("manage move_message_user")
                        self.bot.send_message(
                            message.user.id,
                            emoji.emojize(
                                "{0} {1}: {2}\r\n{3}".format(
                                    EMOJI_MANAGE,
                                    loc("You choosed", message.user.language_ui),
                                    message_user.text,
                                    loc("Now move it to the new position.", message.user.language_ui)
                                ),
                            ),
                            reply_markup=self.get_markup_updown(message.user.language_ui)
                        )

        # if manage is done
        if message.user.is_default_message_type():
            self.repeat_last_message(message.user)

    @staticmethod
    def process_delete_message_user_confirm(user: UserMessage):
        if user.is_set_manage_message():
            message_old = user.get_manage_message()
            message_old.delete_chain()
            return 0
        else:
            return 1

    @staticmethod
    def get_markup_cancel(language_ui, callback):
        button_cancel = types.InlineKeyboardButton(
            text=loc_emoji("Cancel", language_ui, EMOJI_NO),
            callback_data=callback
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(button_cancel)
        return markup

    @staticmethod
    def get_markup_save(language_ui, callback):
        button_save = types.InlineKeyboardButton(
            text=loc_emoji("Save", language_ui, EMOJI_YES),
            callback_data=callback
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(button_save)
        return markup

    @staticmethod
    def get_markup_updown(language_ui):
        button_up = types.InlineKeyboardButton(
            text=loc_emoji("Up", language_ui, EMOJI_UP),
            callback_data="manage move_message_user up"
        )
        button_down = types.InlineKeyboardButton(
            text=loc_emoji("Down", language_ui, EMOJI_DOWN),
            callback_data="manage move_message_user down"
        )
        button_save = types.InlineKeyboardButton(
            text=loc_emoji("Save", language_ui, EMOJI_NO),
            callback_data="manage move_message_user save"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(button_up, button_down)
        markup.add(button_save)
        return markup

    @staticmethod
    def get_markup_yes_no(language_ui, callback_yes, callback_no):
        button_yes = types.InlineKeyboardButton(
            text=loc_emoji("Yes", language_ui, EMOJI_YES),
            callback_data=callback_yes
        )
        button_no = types.InlineKeyboardButton(
            text=loc_emoji("No", language_ui, EMOJI_NO),
            callback_data=callback_no
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(button_yes, button_no)
        return markup

    @staticmethod
    def get_markup_manage(user):
        add_message_user = types.InlineKeyboardButton(
            text=loc_emoji("Add answer", user.language_ui, ":heavy_plus_sign:"),
            callback_data="manage add_message_user"
        )
        delete_message_user = types.InlineKeyboardButton(
            text=loc_emoji("Delete answer", user.language_ui, ":heavy_minus_sign:"),
            callback_data="manage delete_message_user"
        )
        edit_message_user = types.InlineKeyboardButton(
            text=loc_emoji("Edit answer", user.language_ui, ":memo:"),
            callback_data="manage edit_message_user"
        )
        order_message_user = types.InlineKeyboardButton(
            text=loc_emoji("Move answer", user.language_ui, ":input_numbers:"),
            callback_data="manage move_message_user"
        )
        edit_message_bot = types.InlineKeyboardButton(
            text=loc_emoji("Edit bot message", user.language_ui, ":page_with_curl:"),
            callback_data="manage edit_message_bot"
        )
        button_exit = types.InlineKeyboardButton(
            text=loc_emoji("Exit manage mode", user.language_ui, ":locked:"),
            callback_data="manage exit"
        )

        markup = types.InlineKeyboardMarkup()
        if user.level > 0:
            markup.add(add_message_user, delete_message_user)
            markup.add(edit_message_user, order_message_user)
            markup.add(edit_message_bot)
        markup.add(button_exit)

        return markup

    # ADMIN MODE STARTS HERE
    def callback_admin(self, call):
        if call.user.level > 1 and call.message:
            arr = call.data.split()
            if len(arr) > 1:
                if arr[1] == "edit":
                    if len(arr) > 2:
                        if arr[2] == "level":
                            if len(arr) > 4:
                                user_id = arr[3]
                                level = arr[4]
                                user = UserMessage.db_select_user(user_id=user_id)
                                user.set_level(level)
                                self.bot.edit_message_text(
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text=loc_emoji("User level edited.", call.user.language_ui, EMOJI_ADMIN)
                                )
                                self.message_admin(call.user)
                    else:
                        call.user.set_message_type("admin edit select")
                        self.bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=loc_emoji("Enter user's login.", call.user.language_ui, EMOJI_ADMIN),
                            reply_markup=self.get_markup_cancel(call.user.language_ui, "admin cancel")
                        )
                elif arr[1] == "cancel":
                    call.user.reset_message_type()
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("Admin mode", call.user.language_ui, EMOJI_ADMIN),
                        reply_markup=self.get_markup_admin(call.user)
                    )
                elif arr[1] == "exit":
                    call.user.change_mode(0)
                    call.user.reset_message_type()
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=loc_emoji("You exited admin mode.", call.user.language_ui, EMOJI_ADMIN)
                    )
                    self.repeat_last_message(call.user)

    def process_admin(self, message):
        arr = message.user.get_message_type().split()
        if arr[1] == "edit":
            if arr[2] == "select":
                self.process_admin_edit_select(message)

    def process_admin_edit_select(self, message):
        user = UserMessage.db_select_user(username=message.text)
        if user is not None:
            message.user.set_message_type("admin edit user {}".format(user.id))

            markup = types.InlineKeyboardMarkup()
            levels = UserMessage.get_all_levels()
            for key in levels.keys():
                button = types.InlineKeyboardButton(
                    text=loc(levels[key], message.user.language_ui),
                    callback_data="admin edit level {0} {1}".format(user.id, key)
                )
                markup.add(button)

            self.bot.send_message(
                message.user.id,
                emoji.emojize(
                    "{0} {1}\r\n{2}: {3}\r\n{4}: {5}\r\n{6}: {7}\r\n{8}".format(
                        EMOJI_ADMIN,
                        loc("User found!", message.user.language_ui),
                        loc("First name", message.user.language_ui),
                        user.first_name,
                        loc("Last name", message.user.language_ui),
                        user.last_name,
                        loc("Level", message.user.language_ui),
                        UserMessage.level_to_text(user.level),
                        loc("Select a new user level:", message.user.language_ui)
                    ),
                ),
                reply_markup=markup
            )
        else:
            self.bot.send_message(
                message.user.id,
                loc_emoji("Error. No user found.", message.user.language_ui, EMOJI_ADMIN)
            )

    def message_admin(self, user):
        if user.level > 1 and user.mode > 0:
            self.bot.send_message(
                user.id,
                loc_emoji("Admin mode", user.language_ui, EMOJI_ADMIN),
                reply_markup=self.get_markup_admin(user)
            )

    @staticmethod
    def get_markup_admin(user):
        edit_level = types.InlineKeyboardButton(
            text=loc_emoji("Edit user's level", user.language_ui, ":police_officer:"),
            callback_data="admin edit"
        )
        button_exit = types.InlineKeyboardButton(
            text=loc_emoji("Exit admin mode", user.language_ui, ":locked:"),
            callback_data="admin exit"
        )

        markup = types.InlineKeyboardMarkup()
        if user.level > 1:
            markup.add(edit_level)
        markup.add(button_exit)

        return markup
