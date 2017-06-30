import sqlite3 as sql
from datetime import datetime as dt

class DatabaseHandler:

    def __init__(self, db_path):
        self._users_table = "users"
        self._working_table = "working"
        self._logs_table = "logs"
        self._courses_table = "courses"
        self._courses_categories_table = "courses_categories"

        self._dbName = db_path

    def _execute_query(self, query, *args):
        """
            Function that executes a given query, except SELECT queries
        :param query:       the query to be executed
        :param args:        the arguments to be inserted
        :return:
        """

        con = sql.connect(self._dbName)
        cur = con.cursor()
        cur.execute(query, args)
        con.commit()
        con.close()

    def _execute_DELETE(self, table, conds, *args):

        query = "DELETE FROM " + table + " WHERE " + conds
        self._execute_query(query, *args)

    def _execute_INSERT(self, table, cols, *args):
        """
        :param table:       the table to insert into
        :param cols:        the list of columns we want to insert to
        :param items:       the list of items we want to insert
        :return:            -
        """

        query = "INSERT INTO " + table + " ("

        qmarks = "("

        for col in cols:
            qmarks = qmarks + "?"
            query += col
            if col != cols[-1]:
                query += ", "
                qmarks += ", "
            else:
                query += ") "
                qmarks += ") "

        query += "VALUES " + qmarks

        print(query)


        self._execute_query(query, *args)

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

    def start_work(self, email, course):
        """

        :param email:       The email of the user that wants to start to work
        :param course:      The course name
        :return:            - status = True - if it was successful
                                       False - otherwise
                            - message   The error message/ a blank string if it was successful
        """

        try:
            con = sql.connect(self._dbName)
            cur = con.cursor()
            cur.execute("SELECT id FROM users WHERE email='" + email +"';")
            results = list(set(cur.fetchall()))
            con.commit()
            con.close()
        except:
            return False, "Server error"

        if len(results) != 1:
            #Failed! No such email or too many entries
            return False, "Incorrect email!"

        uid = results[0][0]

        try:
            con = sql.connect(self._dbName)
            cur = con.cursor()
            cur.execute("SELECT id FROM courses WHERE name='"+course+"';")
            results = list(set(cur.fetchall()))
            con.commit()
            con.close()

        except:
            return False, "Server error"

        if len(results) != 1:
            #Failed! No such course or too many entries
            return False, "Incorrect course name"

        cid = results[0][0]

        try:
            self._execute_INSERT(self._working_table,
                                ["uid", "working", "since", "cid"],
                                int(uid), 1, dt.now(), int(cid))
        except:
            return False, "Server Error"

        return True, ""

    def stop_work(self, email, time):
        """

        :param email:
        :param time:
        :return:
        """

        try:
            con = sql.connect(self._dbName)
            cur = con.cursor()
            cur.execute("SELECT id FROM users WHERE email='" + str(email) +"';")
            results = list(set(cur.fetchall()))
            con.commit()
            con.close()
        except:
            #Something went wrong when doing the query
            print("aaaa")
            return False, "Server error!"

        if len(results) != 1:
            return False, "Wrong email!"

        uid = results[0][0]
        try:
            con = sql.connect(self._dbName)
            cur = con.cursor()
            cur.execute("SELECT working, cid, since FROM working WHERE uid=" + str(uid))
            results = list(set(cur.fetchall()))
            con.commit()
            con.close()
        except:
            return False, "Server error!"

        if len(results) != 1 or results[0][0] != 1:
            return False, "Not working!"

        cid = results[0][1]

        if time < 0:
            return False, "Incorrect time!"

        try:
            self._execute_DELETE(self._working_table, "uid=?", uid)
            self._execute_INSERT(self._logs_table,
                                ["uid", "cid", "duration"],
                                uid, cid, time)
            print("done the delete")
        except:
            return False, "Server error!"

        return True, ""




