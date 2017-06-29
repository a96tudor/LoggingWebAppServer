import sqlite3 as sql
from exceptions import *

class DatabaseHandler:

    def __init__(self, db_path):
        self._users_table = "users"
        self._working_table = "working"
        self._logs_table = "logs"
        self._courses_table = "courses"
        self._courses_categories_table = "courses_categories"

        self._dbName = db_path


    def _execute_SELECT(self, table, conds, cols=["*"], limit=None, order=None, groupBy=None, *args):
        """
                    function that executes a SELECT query
        :param cols:        the list of columns we want. default ['*']
        :param table:       the table name
        :param conds:       the conditions, as a string
        :param limit:       how many results to return. default None
        :param order:       the way to order the results. default None
        :param groupBy:     the way to group the results. default None
        :return:            the list representing the results of the query
        """

        cols_string = ",".join(cols)
        query = "SELECT " + cols_string + " FROM " + str(table)

        if conds != None:
            query += " WHERE " + str(conds)

        if order != None:
            query += " ORDER BY " + str(order)

        if groupBy != None:
            query += " GROUP BY " + str(groupBy)

        if limit != None:
            query += " LIMIT " + str(limit)

        con = sql.connect(self._dbName)
        cur = con.cursor()
        cur.execute(query, args)
        results = list(set(cur.fetchall()))
        con.commit()
        con.close()

        return results


    def start_work(self, email):

        results = self._execute_SELECT(self._users_table, "email=?", email)





