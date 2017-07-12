import sqlite3 as sql
from datetime import datetime as dt
from dateutil import parser as dt_parse
import datetime
from passlib.hash import pbkdf2_sha256
import secrets

class DatabaseHandler:

    def __init__(self, db_path):
        self._users_table = "users"
        self._working_table = "working"
        self._logs_table = "logs"
        self._courses_table = "courses"
        self._courses_categories_table = "courses_categories"

        self._DEFAULT_TTL = 10  # 2 hours

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

    def _encrypt_pass(self, password):
        """
        :param password:        the password to encrypt
        :return:                the encrypted password
        """
        hash = pbkdf2_sha256.encrypt(password,
                                     rounds=200000,
                                     salt_size=16)
        return hash

    def _check_pass(self, password, hash):
        """
        :param password:        the password to be tested
        :param hash:            the hashed password
        :return:                True - if the passwords match
                                False - otherwise
        """
        return pbkdf2_sha256.verify(password, hash)

    def _execute_DELETE(self, table, conds, *args):
        """
            Method that deletes an entry from a table

        :param table:       the name of the table to delete from
        :param conds:       The conditions used to identify the row we want to delete
        :param args:        The values of the variables used in the conditions
        :return:            -
        """

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

    def _execute_UPDATE(self, table, cols, new_values, conds, conds_args):
        """
            Method that updates a database table

        :param table:           The table we execute the update in
        :param cols:            The columns we update, as a list
        :param new_values:      The new values for the corresponding columns, also as a list
        :param conds:           The conditions to identify the row(s) to update
        :param conds_args:      The arguments for the conditions, as a list!!!
        :return:                -
        """
        query = "UPDATE " + table + " SET "

        for i in range(len(cols)):
            item = str(cols[i]) + "=?"
            if i != len(cols) - 1:
                item += ", "
            else:
                item += " "

            query += item

        query += " WHERE " + conds
        arg = new_values+conds_args

        self._execute_query(query, *arg)

    def _get_user_from_hash(self, hash):
        """
            Method that identifies an user based on the hash of the email

        :param hash:    the hash of the email we're looking for
        :return:        -> A tuple representing the row corresponding to that user
                        -> None: otherwise
        """

        all_users = self._execute_SELECT("users", None)
        for user in all_users:
            email = user[1]
            if self._get_sha256_encryption(email) == hash:
                return user

        return None

    def _get_sha256_encryption(self, plaintext):
        """
            Method that takes a plaintext message and returns its sha256 encryption

        :param plaintext:       The text to encrypt
        :return:                the SHA-256 encryption as a base64 string
        """
        import hashlib
        return hashlib.sha256(plaintext.encode('utf-8')).hexdigest()

    def _execute_SELECT_from_query(self, query, *args):
        """
                Method that executes complex SELECT statements, from a given query

        :param query:       The query to execute
        :param args:        The arguments to replace the '?' wildcards from the query
        :return:            The result of the query, as a list of tuples
        """
        con = sql.connect(self._dbName)
        cur = con.cursor()
        cur.execute(query)
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
            return False, "Email already in use!"

        return True, ""

    def stop_work(self, email, time):
        """

        :param email:           The email of the user that stops working
        :param time:            The time the user spent working
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

        if not isinstance(time, int) or time < 0:
            return False, "Incorrect time!"

        try:
            self._execute_DELETE(self._working_table, "uid=?", uid)
            self._execute_INSERT(self._logs_table,
                                ["uid", "cid", "duration", "started_at", "logged_at"],
                                uid, cid, time, results[0][2], dt.now())
        except:
            return False, "Server error!"

        return True, ""

    def add_user(self, email, name, password, admin):
        """
                Function that inserts a new user into the database

        :param email:       The user's email
        :param name:        The user's name
        :param password:    The user's password
        :param admin:       True -  if the user is admin
                            False - otherwise

        :return:            -> True - if it was successful
                               False - otherwise
                            -> an error message, if necessary
        """
        try:
            users = self._execute_SELECT("users","email='"+email+"'")
        except:
            return False, "Server error"

        if len(users) != 0:
            #The user is already in the database
            return False, "Email already in use"

        try:
            self._execute_INSERT("users",
                                 ["email", "full_name", "password", "admin"],
                                 email,
                                 name,
                                 self._encrypt_pass(password),
                                 1 if admin else 0)
        except:
            return False, "Server error"

        return True, ""

    def verify_user(self, email_hash, password):
        """
                Method that tries to authenticate a given user, based on
            a pair of credentials

        :param email_hash:       The user's hashed email to verify
        :param password:    The user's password to verify
        :return:
            A dictionary witht the following format:
                {
                    "success": <True/ False>,
                    "id": <user_id>,               (only if successful)
                    "name": <user's_name>        (only if successful)
                    "token": <login_token>,      (only if successful)
                    "ttl":   <TTL>,              (only if successful)
                    "message":  <error_message>  (if necessary)
                }
        """

        if not isinstance(email_hash, str):
            return {
                "success": False,
                "message": "Incorrect username or password"
            }

        try:
            user = self._get_user_from_hash(email_hash)
        except:
            return {
                "success":  False,
                "message": "Server error"
            }

        if user is not None and self._check_pass(password, user[3]):
            if user[3] is None:
                return {
                    "success": False,
                    "message": "User not validated"
                }
            else:
                token = secrets.token_hex(64)
                self._execute_INSERT("logged_in",
                                    ["token","uid", "last_login", "TTL"],
                                    token, user[0], dt.now(), self._DEFAULT_TTL
                )
                return {
                    "success": True,
                    "id": self._get_sha256_encryption(user[1]),
                    "name": user[2],
                    "token": token,
                    "ttl": self._DEFAULT_TTL
                }
        else:
            return {
                "success": False,
                "message": "Incorrect username or password"
            }

    def get_courses_list(self):
        """
            Method that returns the list of the courses currently in the database

        :return:    A Python dictionary of the format:

                    {
                        "courses": [
                            {
                                "id": <course_id>,
                                "name": <course_name>
                            }
                            {
                                ...
                            }
                            ...
                        ]
                    }
        """

        try:
            query_results = self._execute_SELECT("courses", None, ["name"])
        except:
            return False, "Server Error!"


        id = 0
        results = {
            "courses": []
        }

        for result in query_results:
            partial_result = {
                "id": id,
                "name": result[0]
            }
            id += 1
            results["courses"].append(partial_result)

        return True, results

    def validate_user(self, email_hash, password):
        """
                Method that takes a new user's hashed email and pass and sets it

        :param email_hash:        The hashed email of the user
        :param password:          The password we want to set for the user
        :return:            A dictionary of the format:

        """
        print("started validation")
        user = self._get_user_from_hash(email_hash)
        print("got user")
        print(user)
        if user is None:
            return False, "Incorrect user hash"

        if not user[3] is None:
            return False, "User's password already set"

        try:
            self._execute_UPDATE("users", ["password"], [self._encrypt_pass(password), ], "id=?", [user[0], ])
        except:
            return False, "Server error"

        return True, ""

    def get_working_users(self):
        """
                Method that returns the users working at the moment.

        :return:    The users currently working, as a dictionary of the format:

                    {
                        "users": [
                            {
                                "id": <id>,
                                "name": <full_name>,
                                "email": <hashed_email>,
                                "since": <working_since>,
                                "course": <course_name>
                            },s
                            ...
                        ]
                    }
        """
        query = "SELECT u.full_name, u.email, c.name, w.since FROM " \
                "working AS w " \
                "INNER JOIN users AS u ON w.uid=u.id " \
                "INNER JOIN courses AS c ON w.cid=c.id ";

        try:
            results = self._execute_SELECT_from_query(query)
        except:
            print("SERVER ERROR!")
            return None

        working_users = {
            "users": list()
        }

        id = 0

        for result in results:
            new_entry = dict()
            new_entry["id"] = id
            new_entry["name"] = result[0]
            new_entry["email"] = self._get_sha256_encryption(result[1])
            new_entry["course"] = result[2]
            new_entry["since"] = result[3]
            id += 1
            working_users["users"].append(new_entry)

        return working_users

    def get_logs(self):
        """
            Method that returns all the logs from the database

        :return:       The logs, as a dictionary of the format:

                    {
                        "users": [
                            {
                                "id": <id>,
                                "name": <full_name>,
                                "email": <hashed_email>,
                                "course": <course_name>,
                                "seconds": <no_of_seconds_worked>,
                                "started": <date&time_the_user_started_working>,
                                "logged": <date&time_the_entry_was_logged>
                            },
                            ...
                        ]
                    }
        """

        query = "SELECT u.full_name, u.email, c.name, l.duration, l.started_at, l.logged_at " \
                "FROM logs AS l " \
                "INNER JOIN users AS u ON l.uid=u.id " \
                "INNER JOIN courses AS c ON l.cid=c.id"

        try:
            results = self._execute_SELECT_from_query(query)
        except:
            print("SERVER ERROR!")
            return None

        logs = {
            "users": list()
        }
        id = 0

        for result in results:
            new_entry = dict()
            new_entry["id"] = id
            new_entry["name"] = result[0]
            new_entry["email"] = self._get_sha256_encryption(result[1])
            new_entry["course"] = result[2]
            new_entry["seconds"] = result[3]
            new_entry["started"] = result[4]
            new_entry["logged"] = result[5]
            logs["users"].append(new_entry)
            id += 1
        return logs

    def is_admin(self, email_hash):
        """
            Method that checks if a user is admin or not, based on the hashed email address

        :param email_hash:      The hashed email address
        :return:                True - if the user is an admin
                                False - otherwise
        """

        user_row = self._get_user_from_hash(email_hash)

        if user_row is None:
            # The user doesn't exist
            return False

        return user_row[-1] == 1

    def is_token_still_valid(self, token):
        """
            Method that checks if a user session is still valid

            :param token:  The login token associated with the session
            :returns:
                    A dictionary of the format:

                    {
                        "success": <True/ False>,
                        "valid":   <True/ False>,       (only if successful)
                        "message": <Error message>      (only if not successful)
                    }
        """

        try:
            login_data = self._execute_SELECT("logged_in", "uid="+str(token), ["last_login", "TTL", "id"])
        except:
            return {
                "success": False,
                "message": "Server error"
            }

        if len(login_data) == 0:
            return {
                "success": True,
                "valid": False
            }

        last_login = dt_parse.parse(login_data[0][0])
        expiry_time = last_login + datetime.timedelta(seconds=login_data[0][1])

        if dt.now() < expiry_time:
            return {
                "success": True,
                "valid": True
            }
        else:
            self._execute_DELETE("logged_in", "id=?", login_data[0][2])
            return {
                "success": True,
                "valid": False
            }

