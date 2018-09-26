import sqlite3

from .utility import exception_info, enquote2


class SQLighter:

    def __init__(self, db):
        self.connection = sqlite3.connect(db)
        self.cursor = self.connection.cursor()

    def db_query(self, query, args=None):
        with self.connection:
            if args is None or args == ():
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, args)
            rows = self.cursor.fetchall()
            return rows

    def db_query_rows(self, query, args=None):
        rows = self.db_query(query, args)
        if len(rows) == 0:
            return None
        else:
            return rows

    def db_query_row(self, query, args=None):
        rows = self.db_query(query, args)
        if len(rows) == 0:
            return None
        else:
            return rows[0]

    def db_query_single(self, query, args=None):
        rows = self.db_query(query, args)
        if len(rows) == 0:
            return None
        else:
            return rows[0][0]

    def db_query_commit(self, query, args):
        try:
            with self.connection:
                self.cursor.execute(query, args)
                self.connection.commit()
        except Exception as ex:
            print("#######" + exception_info(ex))  # TODO: ?
            return None
        else:
            return self.cursor.lastrowid

    def close(self):
        self.connection.close()

    @staticmethod
    def gen_insert(table, **kwargs):
        """Generates DB insert statement"""
        cols = []
        vals = []
        for col, val in kwargs.items():
            cols.append(enquote2(col))
            vals.append(enquote2(str(val)))
        cols = ", ".join(cols)
        vals = ", ".join(vals)
        return "INSERT INTO '%s'(%s) VALUES(%s);" % (
            table, cols, vals)
