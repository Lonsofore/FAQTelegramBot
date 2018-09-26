from faqtelegrambot import DB_PATH
from .SQLighter import SQLighter


POS_MIN = 1  # min order num in db
MESSAGE_EMPTY = "_"  # we can't use an empty string with telegram api


class Message:

    def __init__(self, message_id, text):
        self.id = message_id
        self.text = text

    def is_empty_text(self):
        if self.text == MESSAGE_EMPTY:
            return True
        else:
            return False

    def get_text(self):
        return self.text

    @staticmethod
    def empty():
        return MESSAGE_EMPTY


class MessageUser(Message):

    def __init__(self, message_id, text, pos, message_bot_from):
        super().__init__(message_id=message_id, text=text)
        self.pos = pos
        self.message_bot_from = message_bot_from

    @staticmethod
    def db_select_message_by_id(message_id):
        query = """
            SELECT id, text, pos, message_bot_from
            from messages_user
            WHERE id = ?
        """
        args = (message_id, )
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageUser(
                message_id=row[0],
                text=row[1],
                pos=row[2],
                message_bot_from=row[3]
            )
        else:
            return None

    @staticmethod
    def db_select_messages_by_text(text):
        query = """
            SELECT id, text, pos, message_bot_from
            from messages_user
            WHERE text = ?
            ORDER BY id ASC
        """
        args = (text, )
        db = SQLighter(DB_PATH)
        result = db.db_query_rows(query, args)
        db.close()
        if result is not None:
            messages = []
            for row in result:
                messages.append(
                    MessageUser(
                        message_id=row[0],
                        text=row[1],
                        pos=row[2],
                        message_bot_from=row[3]
                    )
                )
            return messages
        else:
            return None

    @staticmethod
    def db_select_messages_by_from(message_bot_from):
        query = """
            SELECT id, text, pos, message_bot_from
            from messages_user
            WHERE message_bot_from = ?
            ORDER BY pos ASC
        """
        args = (message_bot_from, )
        db = SQLighter(DB_PATH)
        result = db.db_query_rows(query, args)
        db.close()
        if result is not None:
            messages = []
            for row in result:
                messages.append(
                    MessageUser(
                        message_id=row[0],
                        text=row[1],
                        pos=row[2],
                        message_bot_from=row[3]
                    )
                )
            return messages
        else:
            return None

    @staticmethod
    def db_select_message_by_from_pos(message_bot_from, pos):
        query = """
            SELECT id, text, pos, message_bot_from
            from messages_user
            WHERE message_bot_from = ? AND pos = ?
            ORDER BY pos ASC
            LIMIT 1;
        """
        args = (message_bot_from, pos)
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageUser(
                message_id=row[0],
                text=row[1],
                pos=row[2],
                message_bot_from=row[3]
            )
        else:
            return None

    @staticmethod
    def db_update_message(message_id, text, pos, message_bot_from):
        query = """
            UPDATE messages_user 
            SET text=?, pos=?, message_bot_from=?
            WHERE id=?;
        """
        args = (text, pos, message_bot_from, message_id)
        db = SQLighter(DB_PATH)
        res = db.db_query_commit(query, args)
        db.close()
        return res

    @staticmethod
    def db_insert_message(text, pos, message_bot_from):
        query = """
            INSERT INTO messages_user(text, pos, message_bot_from) 
            VALUES(?, ?, ?);
        """
        args = (text, pos, message_bot_from)
        db = SQLighter(DB_PATH)
        message_id = db.db_query_commit(query, args)
        db.close()
        if message_id is not None:
            return MessageUser(message_id=message_id, text=text, pos=pos, message_bot_from=message_bot_from)
        else:
            return None

    @staticmethod
    def db_delete_message(message_id):
        query = """
            DELETE from messages_user
            WHERE id=?;
        """
        args = (message_id, )
        db = SQLighter(DB_PATH)
        res = db.db_query_commit(query, args)
        db.close()
        return res

    @staticmethod
    def db_get_max_pos(message_bot_from):
        messages = MessageUser.db_select_messages_by_from(message_bot_from)
        if messages is not None:
            return len(messages)
        else:
            return POS_MIN

    def update(self, text=None, pos=None, message_bot_from=None):
        if text is not None:
            self.text = text

        if pos is not None:
            self.pos = pos

        if message_bot_from is not None:
            self.message_bot_from = message_bot_from

        MessageUser.db_update_message(self.id, self.text, self.pos, self.message_bot_from)

    def set_text(self, text=None):
        if text is None or text == " ":
            self.update(text=MESSAGE_EMPTY)
        else:
            self.update(text=text)

    def delete(self):
        MessageUser.db_delete_message(self.id)

    def delete_chain(self):
        message_id = self.id
        result = MessageUser.db_delete_message(self.id)
        if result is not None:
            message = MessageBot.db_select_message_by_from(message_id)
            if message is not None:
                message.delete_chain()

    def get_message(self):
        return MessageBot.db_select_message_by_from(self.id)

    def get_message_from(self):
        return MessageBot.db_select_message_by_id(self.message_bot_from)

    def order_up(self):
        if self.pos > POS_MIN:
            message = MessageUser.db_select_message_by_from_pos(self.message_bot_from, self.pos-1)
            message.update(pos=message.pos+1)
            self.update(pos=self.pos-1)
            return 0
        else:
            return 1

    def order_down(self):
        pos_max = MessageUser.db_get_max_pos(self.message_bot_from)
        if self.pos < pos_max:
            message = MessageUser.db_select_message_by_from_pos(self.message_bot_from, self.pos+1)
            message.update(pos=message.pos-1)
            self.update(pos=self.pos+1)
            return 0
        else:
            return 1


class MessageBot(Message):

    def __init__(self, message_id, text, message_user_from):
        super().__init__(message_id=message_id, text=text)
        self.message_user_from = message_user_from

    @staticmethod
    def db_select_message_by_id(message_id):
        query = """
            SELECT id, text, message_user_from
            from messages_bot
            WHERE id = ?;
        """
        args = (message_id, )
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageBot(
                message_id=row[0],
                text=row[1],
                message_user_from=row[2]
            )
        else:
            return None

    @staticmethod
    def db_select_messages_by_text(text):
        query = """
            SELECT id, text, message_user_from
            from messages_bot
            WHERE text = ?
            ORDER BY id ASC;
        """
        args = (text, )
        db = SQLighter(DB_PATH)
        result = db.db_query_rows(query, args)
        db.close()
        if result is not None:
            messages = []
            for row in result:
                messages.append(
                    MessageBot(
                        message_id=row[0],
                        text=row[1],
                        message_user_from=row[2]
                    )
                )
            return messages
        else:
            return None

    @staticmethod
    def db_select_message_by_from(message_user_from):
        query = """
            SELECT id, text, message_user_from
            from messages_bot
            WHERE message_user_from = ?;
        """
        args = (message_user_from, )
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageBot(
                message_id=row[0],
                text=row[1],
                message_user_from=row[2]
            )
        else:
            return None

    @staticmethod
    def db_update_message(message_id, text, message_user_from):
        query = """
            UPDATE messages_bot 
            SET text=?, message_user_from=?
            WHERE id=?;
        """
        args = (text, message_user_from, message_id)
        db = SQLighter(DB_PATH)
        res = db.db_query_commit(query, args)
        db.close()
        return res

    @staticmethod
    def db_insert_message(text, message_user_from):
        query = """
            INSERT INTO messages_bot(text, message_user_from) 
            VALUES(?, ?);
        """
        args = (text, message_user_from)
        db = SQLighter(DB_PATH)
        message_id = db.db_query_commit(query, args)
        db.close()
        if message_id is not None:
            return MessageBot(message_id=message_id, text=text, message_user_from=message_user_from)
        else:
            return None

    @staticmethod
    def db_delete_message(message_id):
        query = """
            DELETE from messages_bot
            WHERE id=?;
        """
        args = (message_id, )
        db = SQLighter(DB_PATH)
        res = db.db_query_commit(query, args)
        db.close()
        return res

    @staticmethod
    def db_insert_message_user(message_id, text):
        pos = MessageUser.db_get_max_pos(message_id) + 1
        message_user = MessageUser.db_insert_message(text, pos, message_id)
        MessageBot.db_insert_message(MESSAGE_EMPTY, message_user.id)
        return message_user

    @staticmethod
    def get_first():
        query = """
            SELECT id, text, message_user_from
            from messages_bot
            WHERE message_user_from is NULL;
        """
        args = None
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            return MessageBot(
                message_id=row[0],
                text=row[1],
                message_user_from=row[2]
            )
        else:
            return None

    def update(self, text=None, message_user_from=None):
        if text is not None:
            self.text = text

        if message_user_from is not None:
            self.message_user_from = message_user_from

        MessageBot.db_update_message(self.id, self.text, self.message_user_from)

    def set_text(self, text=None):
        if text is None or text == " ":
            self.update(text=MESSAGE_EMPTY)
        else:
            self.update(text=text)

    def delete(self):
        return MessageBot.db_delete_message(self.id)

    def delete_chain(self):
        message_id = self.id
        result = MessageBot.db_delete_message(self.id)
        if result is not None:
            messages = MessageUser.db_select_messages_by_from(message_id)
            if messages is not None:
                for message in messages:
                    message.delete_chain()

    def get_messages(self):
        return MessageUser.db_select_messages_by_from(self.id)

    def get_message_from(self):
        return MessageUser.db_select_message_by_id(self.message_user_from)

    def add_message_user(self, text):
        return MessageBot.db_insert_message_user(self.id, text)

    def is_first(self):
        first = MessageBot.get_first()
        if first is not None and first.id == self.id:
            return True
        else:
            return False
