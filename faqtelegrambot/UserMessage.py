from faqtelegrambot import CONFIG, DB_PATH
from .User import User
from .SQLighter import SQLighter
from .Message import MessageUser
from .Message import MessageBot


DEFAULT_LEVEL = 0
DEFAULT_MODE = 0
DEFAULT_MESSAGE_TYPE = ''


class UserMessage(User):

    def __init__(
            self,
            user_id, first_name, last_name, username, language_code,  # telegram data
            language_ui=CONFIG["translate"]["default"], level=DEFAULT_LEVEL  # additional data
    ):
        super().__init__(user_id, first_name, last_name, username, language_code, language_ui, level)

        self.mode = DEFAULT_MODE
        self.message_type = ""
        self.message_bot = None

        self.manage_message = None
    
    @staticmethod
    def db_get_last_message_bot(user_id):
        query = """
            SELECT message_bot_id FROM history
            WHERE user_id=? AND message_bot_id is not NULL 
            ORDER BY id DESC
            LIMIT 1;
        """
        args = (user_id, )
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageBot.db_select_message_by_id(row[0])
        else:
            return None

    @staticmethod
    def db_get_last_message_user(user_id):
        query = """
            SELECT message_user_id FROM history
            WHERE user_id=? AND message_user_id is not NULL 
            ORDER BY id DESC
            LIMIT 1;
        """
        args = (user_id, )
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageUser.db_select_message_by_id(row[0])
        else:
            return None

    @staticmethod
    def db_save_history_message_bot(user_id, message):
        query = """
            INSERT INTO history(date, user_id, message_bot_id) 
            VALUES(date('now'), ?, ?);
        """
        args = (user_id, message.id)
        db = SQLighter(DB_PATH)
        result = db.db_query_commit(query, args)
        db.close()
        return result

    @staticmethod
    def db_save_history_message_user(user_id, message):
        db = SQLighter(DB_PATH)
        query = """
            UPDATE history
            SET message_user_id=?
            WHERE id = (SELECT MAX(id) FROM history WHERE user_id=?)
        """
        args = (message.id, user_id)
        result = db.db_query_commit(query, args)
        db.close()
        return result

    def change_mode(self, mode):
        self.mode = mode

    def reset_mode(self):
        self.mode = DEFAULT_MODE

    def set_message_type(self, message_type):
        self.message_type = message_type

    def reset_message_type(self):
        self.message_type = DEFAULT_MESSAGE_TYPE

    def get_message_type(self):
        return self.message_type

    def is_default_message_type(self):
        if self.message_type == DEFAULT_MESSAGE_TYPE:
            return True
        else:
            return False

    def get_last_message_bot(self):
        return self.db_get_last_message_bot(self.id)

    def get_last_message_user(self):
        return self.db_get_last_message_user(self.id)

    def save_history_message_bot(self, message):
        return self.db_save_history_message_bot(self.id, message)

    def save_history_message_user(self, message):
        return self.db_save_history_message_user(self.id, message)

    def get_manage_message(self):
        return self.manage_message

    def reset_manage_message(self):
        self.manage_message = None

    def set_manage_message(self, message):
        self.manage_message = message

    def is_set_manage_message(self):
        if self.manage_message is not None:
            return True
        else:
            return False
