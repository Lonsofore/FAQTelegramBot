from faqtelegrambot import CONFIG, DB_PATH
from .SQLighter import SQLighter


DEFAULT_LEVEL = 0
DEFAULT_LANG = CONFIG["translate"]["default"]


class User:

    def __init__(
            self,
            user_id, first_name, last_name, username, language_code,  # telegram data
            language_ui=DEFAULT_LANG, level=DEFAULT_LEVEL  # additional data
    ):
        # db data
        self.id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.language_code = language_code
        self.language_ui = language_ui
        self.level = level

        # other data
        self.flood = False

    @staticmethod
    def db_insert_user(
            user=None,
            user_id=None, first_name=None, last_name=None, username=None, language_code=None,
            language_ui=None, level=None
    ):
        query = """
            INSERT INTO users(id, first_name, last_name, username, language_code, language_ui, level) 
            VALUES(?, ?, ?, ?, ?, ?, ?);
        """

        if user is not None:
            args = (
                user.id, user.first_name, user.last_name, user.username, user.language_code,
                user.language_ui, user.level
            )
            db = SQLighter(DB_PATH)
            db.db_query_commit(query, args)
            db.close()
            return 0

        elif user_id is not None:
            args = (
                user_id, first_name, last_name, username, language_code,
                language_ui, level
            )
            db = SQLighter(DB_PATH)
            db.db_query_commit(query, args)
            db.close()
            return 0

        else:
            return 1

    @staticmethod
    def db_update_user(
            user=None,
            user_id=None, first_name=None, last_name=None, username=None, language_code=None,
            language_ui=None, level=None
    ):
        query = """
            UPDATE users 
            SET first_name=?, last_name=?, username=?, language_code=?, language_ui=?, level=?
            WHERE id=?;
        """

        if user is not None:
            args = (
                user.first_name, user.last_name, user.username, user.language_code, user.language_ui, user.level,
                user.id
            )
            db = SQLighter(DB_PATH)
            db.db_query_commit(query, args)
            db.close()
            return 0

        elif user_id is not None:
            args = (
                first_name, last_name, username, language_code, language_ui, level,
                user_id
            )
            db = SQLighter(DB_PATH)
            db.db_query_commit(query, args)
            db.close()
            return 0

        else:
            return 1

    @staticmethod
    def db_select_user(user_id=None, username=None):
        if user_id is not None:
            query = """
                SELECT id,first_name, last_name, username, language_code, language_ui, level  
                FROM users 
                WHERE id=? 
                LIMIT 1;
            """
            args = (user_id, )

        elif username is not None:
            query = """
                SELECT id,first_name, last_name, username, language_code, language_ui, level  
                FROM users 
                WHERE username=? 
                LIMIT 1;
            """
            args = (username, )

        else:
            return None

        db = SQLighter(DB_PATH)
        row = db.db_query_row(query, args)
        db.close()
        if row is not None:
            user = User(
                user_id=row[0],
                first_name=row[1],
                last_name=row[2],
                username=row[3],
                language_code=row[4],
                language_ui=row[5],
                level=row[6]
            )
        else:
            user = None
        return user
        
    @staticmethod
    def db_select_users_count():
        query = """
            SELECT COUNT(id)  
            FROM users;
        """
        db = SQLighter(DB_PATH)
        row = db.db_query_row(query)
        db.close()
        if row is not None:
            count = row[0]
        else:
            count = None
        return count

    @staticmethod
    def db_is_user_exists(user_id):
        query = "SELECT id FROM users WHERE id=? LIMIT 1;"
        args = (user_id, )
        db = SQLighter(DB_PATH)
        rows = db.db_query_rows(query, args)
        db.close()
        if rows is None:
            return False
        else:
            return True

    @staticmethod
    def db_update_level(user_id, level):
        query = """
            UPDATE users
            SET level = ?
            WHERE id = ?
        """
        args = (level, user_id)
        db = SQLighter(DB_PATH)
        db.db_query_commit(query, args)
        db.close()

    @staticmethod
    def db_update_language_ui(user_id, language_ui):
        query = """
            UPDATE users
            SET language_ui = ?
            WHERE id = ?
        """
        args = (language_ui, user_id)
        db = SQLighter(DB_PATH)
        db.db_query_commit(query, args)
        db.close()

    @staticmethod
    def get_all_levels():
        return {
            0: "User",
            1: "Editor",
            2: "Administrator"
        }
        
    @staticmethod
    def get_max_level():
        return 2  # TODO: I know, that's really bad

    @staticmethod
    def get_default_level():
        return DEFAULT_LEVEL

    @staticmethod
    def level_to_text(level):
        levels = User.get_all_levels()
        return levels[level]

    @staticmethod
    def db_check_user(user):
        # insert new user or update user's data
        if not User.db_is_user_exists(user.id):
            User.db_insert_user(user=user)
            return 2
        else:
            User.db_update_user(user=user)
            return 1

    @staticmethod
    def db_init_user(user):
        if User.db_is_user_exists(user.id):
            db_user = User.db_select_user(user.id)
            user.language_ui = db_user.language_ui
            user.level = db_user.level
            user.update_data_db()
            return user
        else:
            User.db_insert_user(user)
            return user

    def init_user(self):
        return User.db_init_user(user=self)

    def update_data_db(self):
        User.db_update_user(user=self)

    def update_data_from_db(self):
        user = self.db_select_user(self.id)  # db data
        self.first_name = user.first_name
        self.last_name = user.last_name
        self.username = user.username
        self.language_code = user.language_code
        self.language_ui = user.language_ui
        self.level = user.level

    def check_user(self):
        return self.db_check_user(self)

    def set_level(self, level):
        self.db_update_level(self.id, level)
        self.level = level

    def set_language_ui(self, language_ui):
        self.language_ui = language_ui
        self.db_update_language_ui(self.id, self.language_ui)

    def __str__(self):
        template = "id: {0}:\n" \
                   "first_name: {1}\n" \
                   "last_name: {2}\n" \
                   "username: {3}\n" \
                   "language_code: {4}\n" \
                   "language_ui: {5}\n" \
                   "level: {6}\n"

        result = template.format(
            self.id,
            self.first_name,
            self.last_name,
            self.username,
            self.language_code,
            self.language_ui,
            self.level
        )

        return result
