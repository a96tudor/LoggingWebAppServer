import sqlite3 as sql
from datetime import datetime as dt
from dateutil import parser as dt_parse
import datetime
from passlib.hash import pbkdf2_sha256
import secrets
import time


class DatabaseHandler:

    def __init__(self, db_path):
        self._users_table = "users"
        self._working_table = "working"
        self._logs_table = "logs"
        self._courses_table = "courses"
        self._courses_categories_table = "courses_categories"

        self._DEFAULT_TTL = 7200  # 2 hours

        self._dbName = db_path

    def _flatten_list(self, input):
        """

        :param input:       A list of lists/ tuples
        :return:            The original list, flatten
        """

        if (isinstance(input, list) or isinstance(input, tuple)):
            if len(input) == 0:
                return list()

            result = list()
            for elm in input:
                result += self._flatten_list(elm)
            return result
        else:
            print(input)
            return [input]

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

    def _execute_SELECT(self, table, conds, cols=["*"], limit=None, order=None, groupBy=None, args=None):
        """
                    function that executes a SELECT query
        :param cols:        the list of columns we want. default ['*']
        :param table:       the table name
        :param conds:       the conditions, as a string
        :param limit:       how many results to return. default None
        :param order:       the way to order the results. default None
        :param groupBy:     the way to group the results. default None
        :param args:        The list of arguments for the query (so that we can use wildcards in the query.
                                default []

        :return:            the list representing the results of the query
        """

        cols_string = ",".join(cols)
        query = "SELECT " + cols_string + " FROM " + str(table)

        if conds is not None:
            query += " WHERE " + str(conds)

        if order is not None:
            query += " ORDER BY " + str(order)

        if groupBy is not None:
            query += " GROUP BY " + str(groupBy)

        if limit is not None:
            query += " LIMIT " + str(limit)

        if args is None:
            args = []

        print(query, conds)
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

    def _get_rating(self, uid, cid):
        """

        :param user_id:             The id of the user that did the rating
        :param course_name:         The course name we want the rating for
        :return:                    A dictionary of the form

                                {
                                    "success": <True/ False>,
                                    "rating": <Rating for that course from the user>,           (only if successful)
                                    "message": <ERROR message>                                  (only if not successful)
                                }
        """

        try:
            rating = self._execute_SELECT("ratings", conds="uid=? AND cid=?", cols=["rating"], args=[uid, cid])
        except:
            return {"success": False, "message": "Database failure"}

        if len(rating) == 0:
            # No rating provided yet
            return {"success": True, "rating": 0}
        else:
            # otherwise, just return the value
            return {"success": True, "rating": rating[0][0]}

    def _get_rating_average_for_course(self, cid):
        """

        :param cid:         The course id we want the rating for
        :return:                    A dictionary of the form:

                                    {
                                        "success": <True/ False>,
                                        "rating": <Average rating for the course>,                  (only if successful)
                                                                                                        (as a float)
                                        "floored_rating": <Floored average rating for the course>   (only if successful),
                                        "count":    <number of ratings for that course>             (only if successful),
                                        "message": <ERROR message>                                  (only if not successful)
                                    }
        """

        query = "SELECT AVG(rating), COUNT(rating) FROM " \
                "ratings WHERE cid=?"

        try:
            average = self._execute_SELECT_from_query(query, cid)
        except:
            return {"success": False, "message": "Invalid course name"}

        return {
            "success": True,
            "rating": average[0][0] if average[0][0] else 0.0,
            "floored_rating": int(average[0][0]) if average[0][0] else 0,
            "count": average[0][1] if average[0][1] else 0
        }

    def _did_user_work_on_course(self, uid, cid):
        """

        :param uid:         ID of the user
        :param cid:         ID of the course
        :return:            True/ False
        """
        query_result = self._execute_SELECT("logs", conds="uid=? AND cid=?", cols=["id"], args=[uid, cid])

        return len(query_result) > 0

    def _delete_logs_based_on_category(self, category_name):
        """
                Method that deletes all the logs based on a category name.
                *IMPORTANT: * only to be used after adding them to the archive!!

        :param category_name:       The name of the category we want to base our delete on
        :return:                    True - if successful
                                    False - otherwise
        """
        query = "DELETE FROM logs AS l " \
                "WHERE l.cid IN (" \
                    "SELECT c.id " \
                        "FROM courses AS c " \
                        "INNER JOIN course_catergories AS cc " \
                    "WHERE cc.category_name = ?" \
                ")"

        try:
            self._execute_query(query, category_name)
        except:
            return False

        return True

    def _create_partial_archive(self, conds, value, reason):
        """
                Method that archives logs based on the conditions provided

        :param conds:           The conditions we test when we extract the data
        :param value:          The values we test the columns against
        :param reason:          The reason why we archive the data

        :return:                True - if successful
                                False - otherwise
        """
        select_query = "SELECT u.name, u.email, c.name, c.url, c.description, cc.category_name, l.duration, " \
                        "l.started_at, l.logged_at " \
                            "FROM logs AS l " \
                            "INNER JOIN courses AS c " \
                                "ON l.cid = c.id " \
                            "INNER JOIN course_categories AS cc " \
                                "ON c.cid = cc.id " \
                             "INNER JOIN users AS u " \
                                "ON u.id = l.uid " \
                        "WHERE " + conds + ";" \

        try:
            raw_data = self._execute_SELECT_from_query(select_query, value)
        except:
            return False


        return self._insert_into_archive(raw_data, reason)

    def _insert_logs_into_archive(self, partial_data, reason):
        """
            Method that inserts data into the archive

        :param partial_data:            partial data (i.e. without archive date and reason)
        :param reason:                  the reason for archiving

        :return:                        True - if successful
                                        False - otherwise
        """
        data_to_archive = list()

        extra_data = (dt.now(), reason)

        for entry in partial_data:
            data_to_archive.append(entry + extra_data)

        insert_query = "INSERT INTO logs_archive (" \
                            "user_name, user_email, " \
                            "course_name, course_url, course_description, course_category, " \
                            "worked_for, started_at, logged_at, " \
                            "archived_at, reason" \
                       ") VALUES (?,?,?,?,?,?,?,?,?,?,?)"

        try:
            conn = sql.connect(self._dbName)
            cur = conn.cursor()
            cur.executemany(insert_query, data_to_archive)
            conn.commit()
        except:
            return False
        finally:
            conn.close()

        return True

    def _get_courses_user_worked_on(self, uid):
        """
            Private method that returns an aggregate list of courses the user worked on, and the rating he/she gave to
        every specific course (if any)

        :param uid:         the uid of the user (corresponding to the uid from the database)

        :return:            A dictionary with the following format:

                        {
                            "success": <True/ False>,
                            "courses": [                                    (only if successful)
                                {
                                    "id": <id of the entry>,
                                    "name": <course name>,
                                    "link": <course link>,
                                    "worked_for": <time spent working on that course (HH:MM:SS)>,
                                    "rating": <rating given to the course>,
                                    "rated_at": <date the rating was last updated>
                                },
                                {
                                    ...
                                },
                                ...
                            ],
                            "message": <ERROR message>                      (only if not successful)
                        }
        """
        query = "SELECT c.name, c.url, SUM(l.duration), " \
                        "(CASE r.rating " \
                            "WHEN r.rating IS NOT NULL THEN r.rating " \
                            "ELSE 0 " \
                            "END ), " \
                        "(CASE r.rated_at " \
                            "WHEN r.rated_at IS NOT NULL THEN r.rated_at " \
                            "ELSE '-' " \
                        "END) " \
                    "FROM logs AS l " \
                    "INNER JOIN users AS u " \
                        "ON u.id = l.uid " \
                    "INNER JOIN courses AS c " \
                        "ON c.id = l.cid " \
                    "LEFT OUTER JOIN ratings AS r " \
                        "ON r.uid = u.id AND r.cid = c.id " \
                "WHERE u.id=? " \
                "GROUP BY c.id;"


        courses = self._execute_SELECT_from_query(query, uid)

        result = {
            "success": True,
            "courses": list()
        }
        id = 1

        for course in courses:
            new_entry = {
                "id": id,
                "name": course[0],
                "link": course[1],
                "worked_for": time.strftime('%H:%M:%S', time.gmtime(course[2])),
                "rating": course[3],
                "rated_at": course[4]
            }
            result["courses"].append(new_entry)
            id += 1

        return result

    def get_categories_list(self):
        """

        :return:                A dictionary with the following form:
                                {
                                    "success":  <True/ False>,
                                    "categories": [                                 (only if successful)
                                        {
                                            "id": <id of the list entry>,
                                            "category_name": <name of the new category>
                                        }
                                    ],
                                    "message": <ERROR message>                      (only if not successful)
                                }
        """

        try:
            categories = self._execute_SELECT(table="course_categories", conds=None, cols=["category_name"])
        except:
            return {"success": False, "message": "Database failure"}

        result = {
            "success": True,
            "categories": list()
        }
        id = 1

        for category in categories:
            new_entry = {
                "id": id,
                "category_name": category[0]
            }
            result["categories"].append(new_entry)
            id += 1

        return result

    def start_work(self, email_hash, course):
        """

        :param email_hash:       The email hash of the user that wants to start to work
        :param course:           The course name
        :return:                 - status = True - if it was successful
                                            False - otherwise
                                 - message   The error message/ a blank string if it was successful
        """

        try:
            user = self._get_user_from_hash(email_hash)
        except:
            return False, "Server error"

        if user is None:
            return False, "Incorrect email!"

        uid = user[0]

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

    def stop_work(self, email_hash, time):
        """

        :param email_hash:           The email hash of the user that stops working
        :param time:                 The time the user spent working
        :return:
        """



        try:
            user = self._get_user_from_hash(email_hash)
        except:
            return False, "Server error"

        if user is None:
            return False, "Incorrect email!"

        uid = user[0]

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

    def signup(self, email, name, password, admin):
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

    def user_login(self, email, password):
        """
                Method that tries to authenticate a given user, based on
            a pair of credentials

        :param email_hash:       The user's email to verify
        :param password:    The user's password to verify
        :return:
            A dictionary with the following format:
                {
                    "success": <True/ False>,
                    "id": <user_id>,               (only if successful or if user not validated)
                    "name": <user's_name>        (only if successful)
                    "token": <login_token>,      (only if successful)
                    "ttl":   <TTL>,              (only if successful),
                    "is_admin": <whether the user logging in is an admin or not>      (only if successful)
                    "message":  <error_message>  (if necessary)
                }
        """

        if not isinstance(email, str):
            return {
                "success": False,
                "message": "Incorrect username or password"
            }


        user = self._execute_SELECT("users", conds="email=?", args=[email])


        if user is not None and len(user) != 0:
            user = user[0]
            if user[3] is None:
                return {
                    "success": False,
                    "id": self._get_sha256_encryption(email),
                    "message": "User not validated"
                }
            elif self._check_pass(password, user[3]):

                def get_new_token(ttl):
                    """
                        Inner function that creates a unique session token for the user

                    :return:
                    """
                    token = secrets.token_hex(64)
                    self._execute_INSERT("logged_in",
                                         ["token", "uid", "last_login", "TTL"],
                                         token, user[0], dt.now(), self._DEFAULT_TTL
                                         )
                    return {
                        "success": True,
                        "id": self._get_sha256_encryption(user[1]),
                        "name": user[2],
                        "token": token,
                        "ttl": ttl,
                        "is_admin": user[4] == 1
                    }

                logged_in = self._execute_SELECT("logged_in", conds="uid=?", cols=["token"], args=[user[0]])
                if len(logged_in) == 0:
                    return get_new_token(self._DEFAULT_TTL)
                else:
                    valid = self.is_token_still_valid(logged_in[0][0])
                    if valid["success"] and valid["valid"]:
                            return {
                                "success": True,
                                "id": self._get_sha256_encryption(user[1]),
                                "name": user[2],
                                "token": logged_in[0][0],
                                "ttl": self._DEFAULT_TTL,
                                "is_admin": user[4] == 1
                            }
                    else:
                        return get_new_token(self._DEFAULT_TTL)
            else:
                return {
                    "success": False,
                    "message": "Incorrect username or password"
                }
        else:
            return {
                "success": False,
                "message": "Incorrect username or password"
            }

    def get_courses_list(self, user_id):
        """
            Method that returns the list of the courses currently in the database

        :param user_id:     The id of the user asking for the list
                                (used in order to take into account the rights of the user;
                                        i.e. courses the user is allowed to access)

        :return:    A Python dictionary of the format:

                    {
                        "success": <True/False>,
                        "courses": [
                            {
                                "id": <course_id>,
                                "name": <course_name>,
                                "url": <url_of_the_course>
                            }
                            {
                                ...
                            }
                            ...
                        ],                                           (only if successful)
                        "message": <ERROR message>                   (only if not successful)
                    }
        """

        user = self._get_user_from_hash(user_id)

        if user is None:
            return {"success": False, "message": "Invalid user ID"}

        uid = user[0]

        query = "SELECT c.name, c.url " \
                "FROM courses AS c " \
                    "INNER JOIN rights AS r " \
                "ON c.cid = r.cid " \
                "WHERE r.uid=?;"

        try:
            query_results = self._execute_SELECT_from_query(query, uid)
        except:
            return {"success": False, "message": "Database failure"}


        id = 1
        results = {
            "success": True,
            "courses": list()
        }

        for result in query_results:
            partial_result = {
                "id": id,
                "name": result[0],
                "url": result[1]
            }
            id += 1
            results["courses"].append(partial_result)

        return results

    def validate_user(self, email_hash, password):
        """
                Method that takes a new user's hashed email and pass and sets it

        :param email_hash:        The hashed email of the user
        :param password:          The password we want to set for the user
        :return:            A dictionary of the format:

        """
        user = self._get_user_from_hash(email_hash)
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
                        "success": <True/ False>
                        "users": [                                          (only if successful)
                            {
                                "id": <id>,
                                "name": <full_name>,
                                "email": <actual email>,
                                "since": <working_since>,
                                "worked_for":   <last logged time for that user>,
                                "course": <course_name>,
                                "user_details_function":  <JS function to be called in order to get more user details>,
                                "mailto_link":  <link to enable mailto function>,
                                "stop_work_function": <JS function to be called when we want to stop work>,
                                "course_details_function": <JS function to be called when we want more details on the course>
                            },
                            ...
                        ],
                        "message": <ERROR message>                          (only if not successful)
                    }
        """
        query = "SELECT u.full_name, u.email, c.name, w.since, w.time " \
                    "FROM working AS w " \
                    "INNER JOIN users AS u " \
                        "ON w.uid=u.id " \
                    "INNER JOIN courses AS c " \
                        "ON w.cid=c.id ";

        try:
            results = self._execute_SELECT_from_query(query)
        except:
            return {"success": False, "message": "Database failure"}

        working_users = {
            "success": True,
            "users": list()
        }

        id = 1

        for result in results:
            new_entry = dict()
            new_entry["id"] = id
            new_entry["name"] = result[0]
            new_entry["email"] = result[1]
            new_entry["course"] = result[2]
            new_entry["since"] = result[3]
            new_entry["worked_for"] = result[4]
            new_entry["user_details_function"] = "get_user_details('" + self._get_sha256_encryption(result[1]) + "')"
            new_entry["mailto_link"] = "mailto:" + result[1]
            new_entry["stop_work_function"] = "stop_work('" + self._get_sha256_encryption(result[1]) + "')"
            new_entry["course_details_function"] = "get_course_details('" + result[2] + "')"
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
            login_data = self._execute_SELECT("logged_in", "token='"+str(token)+"'", ["last_login", "TTL"])
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
            self._execute_DELETE("logged_in", "token=?", token)
            return {
                "success": True,
                "valid": False
            }

    def logout_user(self, email_hash):
        """

        :param email_hash:      The hashed email of the user
        :return:                A dictionary of the format:

                    {
                        "success": <True/False>,
                        "message": <ERROR_message>          (only if not successful)
                    }
        """
        try:
            uid = self._get_user_from_hash(email_hash)
        except:
            return {
                "success": False,
                "message": "Server error when finding user"
            }

        print("USER DETAILS: ", uid)

        try:
            self._execute_DELETE("logged_in", "uid=?", uid[0])
        except:
            return {
                "success": False,
                "message": "Server error when deleting"
            }

        return {"success": True}

    def get_history_for_user(self, email_for_request, email_for_user):
        """
            Method that gets the history for a user, but the request is made by another user

        :param email_for_request:       The email hash of the user making the request.
                                        It will only work if the user is an admin

        :param email_for_user:          The email hash of the user we want the history for

        :return:                        A dictionary of the format:

                        {
                            "success": <True/False>,
                            "user": <name_of_the_user_whose_history_we_have>    (only if successful)
                            "history": [                                        (only if successful)
                                {
                                    "id": <entry_id>,
                                    "course_name": <Course_name>,
                                    "course_url": <course_url>,
                                    "started_at": <started_at>,
                                    "logged_at": <time_entry_was_logged>,
                                    "time":  <no_of_seconds_spent_working>,
                                    "course-rating": <rating from the user for that specific course>
                                },
                                { ... },
                                ...
                            ],
                            "total": <total_worked_by_the_user>                 (only if successful)
                            "message": <ERROR_message>                          (only if not successful)
                        }
        """
        if not self.is_admin(email_for_request) and email_for_request != email_for_user:
            return {
                "success": False,
                "message": "Not enough privileges"
            }

        try:
            user = self._get_user_from_hash(email_for_user)
        except:
            return {
                    "success": False,
                    "message": "Server error - hash"
            }

        if user is None:
            return {
                "success": False,
                "message": "Invalid user ID"
            }

        uid = user[0]

        query = "SELECT c.name, c.url, l.started_at, l.duration, l.logged_at, c.id " \
                "FROM logs AS l " \
                "INNER JOIN courses AS c ON l.cid = c.id " \
                "WHERE l.uid=" + str(uid) + ";"

        try:
            results = self._execute_SELECT_from_query(query)
        except:
            return {
                "success": False,
                "message": "Server error - SELECT"
            }

        response = {
            "user": user[2],
            "success": True,
            "history": list()
        }

        id = 1
        total = 0

        results = sorted(results, key=lambda x: x[2] if x[2] else "")

        for result in results:
            if result[2] is None or result[4] is None:
                continue

            rating = self._get_rating(uid, result[5])

            response["history"].append({
                    "id": id,
                    "course_name": result[0],
                    "course_url": result[1],
                    "started_at": result[2][:-7],
                    "logged_at": result[4][:-7],
                    "time": time.strftime('%H:%M:%S', time.gmtime(result[3])),
                    "rating": rating["rating"] if rating["success"] else 0
                })

            id += 1
            total += result[3]

        response["total"] = time.strftime('%H:%M:%S', time.gmtime(total))

        response["history"] = sorted(response["history"],
                                     key=lambda x: x["started_at"])
        return response

    def get_stats_for_user(self, email_for_request, email_for_user):
        """

        :param email_for_request:       The email hash of the user making the request.
                                        It will only work if the user is an admin

        :param email_for_user:          The email hash of the user we want the history for

        :return:                        A dictionary of the format:

                                    {
                                        "success": <True/ False>,
                                        "seconds": <no_of_seconds_worked>,      (only if successful)
                                        "message": <ERROR_message>              (only if not successful)
                                    }
        """
        if not self.is_admin(email_for_request) and email_for_request != email_for_user:
            return {
                "success": False,
                "message": "Not enough privileges"
            }

        try:
            user = self._get_user_from_hash(email_for_user)
        except:
            return {
                    "success": False,
                    "message": "Server error"
            }

        if user is None:
            return {
                "success": False,
                "message": "Invalid user ID"
            }

        uid = user[0]

        query = "SELECT SUM(l.duration) FROM logs AS l WHERE l.uid=?;"

        try:
            results = self._execute_SELECT_from_query(query, uid)
        except:
            return {
                "success": False,
                "message": "Server error"
            }

        if len(results) == 0:
            return {
                "success": True,
                "seconds": 0
            }

        return {
            "success": True,
            "seconds": results[0][0]
        }

    def get_leaderboard(self):
        """

        :return:    The leader board based on the data we have so far in the database.

                    It will be an dictionary of the format:
                            {
                                "success": <True/False>,
                                "leader_board": [                               (only if successful)
                                    {
                                        "id": <entry_id>,
                                        "name": <user's_full_name>,
                                        "user_id": <user's_email_hash>,
                                        "seconds": <number_of_seconds_worked>
                                    },
                                    {...},
                                    ...
                                ],
                                "total":   <total_hrs_worked>                   (only if successful
                                "message": <ERROR_message>                      (only if not successful)

                            }
        """
        query = "SELECT u.full_name, u.id, u.email, TOTAL(l.duration) AS tot " \
                "FROM users AS u " \
                "LEFT OUTER JOIN logs AS l ON u.id = l.uid " \
                "GROUP BY u.id " \
                "ORDER BY tot DESC;"

        try:
            users = sorted(self._execute_SELECT_from_query(query),
                            key=lambda user: -1.0 * user[3])
        except:
            return {
                "success": False,
                "message": "Server error"
            }

        result = {
            "success": True,
            "leader_board": list()
        }

        id = 1
        total = 0

        for user in users:
            result["leader_board"].append( {
                    "id": id,
                    "name": user[0],
                    "user_id": self._get_sha256_encryption(user[2]),
                    "seconds": time.strftime('%H:%M:%S', time.gmtime(user[3]))
            })
            id += 1
            total += user[3]

        result["total"] = time.strftime('%H:%M:%S', time.gmtime(total))

        return result

    def get_courses_list_with_details(self, user_id):
        """
                Method that returns a list of courses, with details

        :param user_id:     The id of the user asking for the course list
                        Required in order to only display the courses that the user
                                    is allowed to access

        :return:    a dictionary of the format:

                    {
                        "success": <True/ False>,
                        "courses": [                                                    (only if successful)
                            {
                                "id": <entry_id>,
                                "name": <course_name>,
                                "url": <course_url>,
                                "syllabus": <course_syllabus>,
                                "about": <course_about>,
                                "notes": <course_notes>,
                                "commitment_low": <minimum_weekly_commitment>,
                                "commitment_high": <maximum_weekely_commitment>,
                                "weeks": <number_of_weeks_required>,
                                "category": <category_name>,
                                "rating": {
                                    "success":  <True/ False>,
                                    "rating":   <floating point average rating for the course>,
                                    "floored_rating" <floored average rating for the course>,
                                    "count": <number of ratings for this course>,
                                    "message": <ERROR message>          (only if rating function is not successful)
                                }
                            },
                            {...},
                            ...
                        ],
                        "message": <ERROR_message>                                      (only if not successful)
                    }
        """

        user = self._get_user_from_hash(user_id)

        if user is None:
            return {"success": False, "message": "Invalid user ID"}

        uid = user[0]

        query = "SELECT c.name, c.url, c.syllabus, c.about, c.notes, " \
                    "c.weekly_commitment_low, c.weekly_commitment_high, c.number_weeks, cc.category_name, c.id " \
                "FROM courses AS c " \
                "INNER JOIN course_categories AS cc ON c.cid = cc.id " \
                "INNER JOIN rights AS r ON cc.id=r.cid " \
                "WHERE r.uid =?"

        try:
            courses = self._execute_SELECT_from_query(query, uid)
        except:
            return {
                "success": False,
                "message": "Server error"
            }

        result = {
            "success": True,
            "courses": list()
        }

        id = 1

        for course in courses:
            new_entry = {
                    "id": id,
                    "name": course[0],
                    "url": course[1],
                    "syllabus": course[2],
                    "about": course[3],
                    "notes": course[4],
                    "commitment_low": course[5],
                    "commitment_high": course[6],
                    "weeks": course[7],
                    "category": course[8],
                    "function": "start_work('" + course[0] + "','" + course[1] + "');",
                    "rating": 0,
                    "worked_on": False
                }
            result["courses"].append(new_entry)
            id += 1
        return result

    def add_user(self, id_adder, email, full_name, admin, rights):
        """

        :param id_adder:            The id of the person adding the user (Has to be an admin)
        :param email:               The email of the person that is added
        :param full_name:           The full name of the person that is added
        :param admin:               Whether the person that is added is an admin/ not (1/0)
        :param rights:              The list of rights for the user

        :return:                    A dictionary of the format:
                                {
                                    "success": <True/False>,
                                    "user_id": <the id of the new user, in order to generate the validation link>, (only if successful)
                                    "message": <ERROR message>          (only if not successful)
                                }
        """
        if not self.is_admin(id_adder):
            return {"success": False, "message": "You don't have enough rights for this."}

        try:
            self._execute_INSERT("users", ["email", "full_name", "admin"], email, full_name, admin)
        except:
            return {"success": False, "message": "Server error"}

        user_id = self._get_sha256_encryption(email)

        sts, msg = self.set_user_rights(user_id, rights, True)

        if sts:
            return {
                "success": True,
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": msg
            }

    def user_is_working(self, id_user):
        """
                Method that checks whether an user is working or not

        :param id_user:     the id of the user
        :return:            A dictionary of the form:
                        {
                            "success": <True/ False>,
                            "working": <True/ False>,       (only if successful)
                            "course": <course_name>,        (only if successful and working)
                            "time": <no_of_seconds_working> (only if successful and working)
                            "since": <start date>           (only if successful and working)
                            "message": <ERROR_message>      (only if not successful),
                            "function_forced_stop": <the function called on client to force work stopping>
                                                                (only if successful and working)
                            "function_continue":    <the function called on client to continue working>
                                                                (only if successful and working)
                        }
        """
        try:
           user = self._get_user_from_hash(id_user)
        except:
            return {"success": False, "message": "Server error"}

        if user is None:
            return {"success": False, "message": "Invalid user id"}

        try:
            query = "SELECT c.course_name, w.time, w.since " \
                    "FROM working AS w " \
                    "INNER JOIN courses AS c " \
                        "ON w.cid = c.id " \
                    "WHERE w.uid=? AND w.working=1"

            result = self._execute_SELECT_from_query(query, user[0])
        except:
            return {"success": False, "message": "Server error"}

        if len(result) == 0:
            return {"success": True, "working": False}

        return {
            "success": True,
            "working": True,
            "course": result[0][0],
            "time": result[0][1],
            "since": result[0][2],
            "function_forced_stop": "forcedStopWork(" + str(result[0][1]) + ");",
            "function_continue": "continueWork(" + str(result[0][1]) + ");"
        }

    def update_time(self, id_user, time):
        """
            Method that updates the time data for a working user

        :param id_user:     The id of the working user
        :param time:        The working time  (in seconds)
        :return:            status - True if successful
                                   - False if not
                            message - the ERROR message / "" if successful
        """
        try:
           user = self._get_user_from_hash(id_user)
        except:
            return False, "Server error"

        if user is None:
            return False, "Invalid user ID"

        id = user[0]

        try:
            self._execute_UPDATE("working", ["time"], [time], "uid=?", [id])
        except:
            return False, "User not working"

        return True, ""

    def get_user_details(self, id_asker, id_user):
        """

        :param id_asker:        The id of the user asking for the details
        :param id_user:         The id of the user we want the information for
        :return:                A dictionary of the format:
                        {
                            "success": <True/False>,
                            "admin":   <True/False>,        (only if successful)   --- if the asker is admin
                            "name":    <user's name>,       (only if successful)
                            "email":   <user's email>       (only if successful and asker is admin)
                            "is_admin": <True/False>,       (only if successful and asker is admin)
                            "access":   [                   (only if successful and asker is admin)
                                {
                                    "id": <id of entry>,
                                    "category": <name of category>,
                                    "has_access": <True/ False>
                                },
                                {
                                    ...
                                },
                                ...
                            ],
                            "courses": [    <list of courses the user worked on>
                                *NOTE: * see _get_courses_worked_on() documentation for more details
                            ]
                            "message":  <ERROR_message>     (only if not successful)
                        }
        """
        if not (self.is_admin(id_asker) or id_asker == id_user):
            return {
                "success": False, "message": "Not enough rights to do this!"
            }

        user = self._get_user_from_hash(id_user)

        if user is None:
            return {
                "success": False, "message": "Invalid user id!"
            }



        if self.is_admin(id_asker):
            raw_rights = self.get_user_rights(user_id=id_user)
            rights = [x["category_name"] for x in raw_rights["rights"]] if raw_rights["success"] else None
            categories = self.get_categories_list()
            courses = self._get_courses_user_worked_on(user[0])
            print(courses)

            return {
                "success": True,
                "admin": True,
                "name": user[2],
                "email": user[1],
                "access": [{"id": "cb" + str(x["id"]), "name": x["category_name"], "has_access": x["category_name"] in rights}
                                    for x in categories["categories"]] if categories["success"] else None,
                "courses": courses["courses"] if courses["success"] else 0
            }
        else:
            return {
                "success": True,
                "admin": False,
                "name": user[2],
                "access": rights["rights"] if rights["success"] else 0
            }

    def update_user_name(self, id_updater, id_user, new_name):
        """

        :param id_updater:          The id of the person who's updating the name.
                                It has to be either an admin, or the same as the id_user
        :param id_user:             The id of the user we update the name for
        :param new_name:            the new name for the user
        :return:                 A dictionary of the format:
                        {
                            "success": <True/False>,
                            "message": <ERROR_message> (only if not successful)
                        }
        """
        if not (self.is_admin(id_updater) or id_updater == id_user):
            return {
                "success": False, "message": "Not enough rights to do it"
            }

        user = self._get_user_from_hash(id_user)

        if user is None:
            return {
                "success": False, "message": "Invalid user id"
            }

        uid = user[0]

        try:
            self._execute_UPDATE("users", ["full_name"], [new_name], "id=?", [uid])
        except:
            return {
                "success": False, "message": "Database failure"
            }

        return {"success": True}

    def update_user_password(self, id_user, old_password, new_password):

        """
            Method that updates a user's password. Only works with the same user doing it

        :param id_user:                 the id of the user we update the password for
        :param old_password:            the old password (for validation)
        :param new_password:            the new password
        :return:                        A dictionary with the following format:
                            {
                                "success":  <True/ False>,
                                "message": <ERROR_message>  (only if not successful)
                            }
        """
        user = self._get_user_from_hash(id_user)
        if user is None:
            return {
                "success": False, "message": "Incorrect user ID"
            }

        if self._check_pass(old_password, user[3]):
            try:
                self._execute_UPDATE("users", ["password"], [self._encrypt_pass(new_password)], "id=?", [user[0]])
            except:
                return {
                    "success": False,
                    "message": "Database failure"
                }

            return {"success": True}

        return {"success": False, "message": "Invalid password"}

    def update_user_password_as_admin(self, id_admin, id_user, new_password):
        """
                Method that allows an admin to update a user's password

        :param id_admin:            The id of the admin doing the update
        :param id_user:             The id of the user doing the update for
        :param new_password:        The new password
        :return:                    A dictionary with the following format:
                        {
                            "success": <True/ False>
                            "message": <ERROR_message>      (only if not successful)
                        }
        """
        if not (self.is_admin(id_admin)):
            return {
                "success": False,
                "message": "Not enough rights to do this"
            }

        user = self._get_user_from_hash(id_user)

        if user is None:
            return {
                "success": False,
                "message": "Invalid user id"
            }

        try:
            self._execute_UPDATE("users", ["password"], [self._encrypt_pass(new_password)], "id=?", [user[0]])
        except:
            return {
                "success": False,
                "message": "Database failure"
            }

        return {"success": True}

    def force_stop_work(self, id_asker, id_user):
        """
            Method that stops a user working based on the logged time in the database

        :param id_user:         the id of the user we want to stop
        :return:                - status: <True/ False>
                                - message: <ERROR_message> if anything goes wrong
        """

        if not (self.is_admin(id_asker) or id_user == id_asker):
            return False, "Not enough rights to perform the action"

        user = self._get_user_from_hash(id_user)

        if user is None:
            return False, "Invalid user id"

        id = user[0]

        try:
            time = self._execute_SELECT("working", "uid="+str(id), ["time"])
        except:
            return False, "Server error"

        if len(time) == 0:
            return False, "User not working"
        else:
            return self.stop_work(id_user, time[0][0])

    def set_user_rights(self, user_id, rights, first_time):
        """

                Method that sets the rights for a user.
                It follows these steps:

                        (1) DELETES all the old rights of the user
                        (2) INSERTS the new rights into the database

        :param user_id:         ID of the user doing the update for
        :param rights:          The list of rights for that specific user
                                *Note: ["*"] means rights for all course categories*
        :param first_time:      Whether it is the first time when we set the rights for the user.

        :return:                - status:   <True/ False>
                                - message:  <ERROR message> (only if status=False)
        """

        user = self._get_user_from_hash(user_id)

        if user is None:
            return False, "Incorrect user ID"

        uid = user[0]

        if not first_time:
            try:
                self._execute_DELETE("rights", "uid=?", uid)
            except:
                return False, "Database failure"

        if rights == ["*"]:
            # Adding rights for all course categories
            try:
                categories = self._flatten_list(
                    self._execute_SELECT("course_categories", None, ["id"])
                )
            except:
                print("error getting categories")
                return False, "Database failure"
        else:
            # Adding only the ids of the categories from the list
            categories = list()
            for right in rights:
                try:
                    id = self._execute_SELECT(table="course_categories", conds="category_name=?", cols=["id"], args=[right])
                except:
                    return False, "Database failure"

                if len(id):
                    categories.append(id[0][0])

        print(categories)
        for cid in categories:
            print(uid, cid)
            self._execute_INSERT("rights", ["uid", "cid"], uid, cid)
            try:
                #self._execute_INSERT("rights", ["uid", "cid"], uid, cid)
                print("Test")
            except:
                print("Error setting rights")
                return False, "Database failure"

        return True, ""

    def get_user_rights(self, user_id):
        """
            Method that gets the rights of a user

        :param user_id:     The id of the user we want the info for
        :return:            A dictionary with the following format:

                        {
                            "success":  <True/ False>,
                            "rights":  [
                                {
                                    "category_id": <ID of a category that the user is allowed to access>,
                                    "category_name": <name of a category the user has access to>
                                }
                            ],                                      (only if successful)
                            "message":  <ERROR_message>             (only if not successful)
                        }
        """

        user = self._get_user_from_hash(user_id)

        if user is None:
            return {"success": False, "message": "Invalid user ID"}

        uid = user[0]

        query = "SELECT c.id, c.category_name " \
                "FROM rights AS r " \
                    "INNER JOIN course_categories AS c " \
                "ON r.cid=c.id " \
                "WHERE r.uid=?"

        try:
            categories = self._execute_SELECT_from_query(query, uid)
        except:
            return {"success": False, "message": "Database failure"}

        result = {
            "success": True, "rights": list()
        }

        for category in categories:
            new_entry = {
                "category_id": category[0],
                "category_name": category[1]
            }
            result["rights"].append(new_entry)

        return result

    def add_rating(self, user_id, course_name, rating_value):
        """

        :param user_id:             The id of the user adding the rating
        :param course_name:         The name of the course adding the rating for
        :param rating:              The rating for the course. Has to be between 0 and 5

        :return:                    - success: True/ False
                                    - message: ERROR message (if not successful)
                                               "" otherwise
        """
        user = self._get_user_from_hash(user_id)

        if user is None:
            return False, "Invalid user ID"

        uid = user[0]

        try:
            course = self._execute_SELECT("courses", conds="name=?", cols=["id"], args=[course_name])
        except:
            return False, "Database failure"

        if len(course) == 0:
            return False, "Invalid course name"

        cid = course[0][0]

        try:
            rating = self._execute_SELECT("ratings", conds="uid=? AND cid=?", args=[uid, cid])
        except:
            return False, "Database failure"

        if not (isinstance(rating_value, int) and rating_value >= 0 and rating_value <= 5):
            return False, "Illegal rating value"

        if len(rating) == 0:
            # No previous rating for this course, so insert new entry
            try:
                self._execute_INSERT("ratings", ["uid", "cid", "rating"], uid, cid, rating_value)
            except:
                return False, "Database failure"
            return True, ""
        else:
            # We have to update the entry
            id = rating[0][0]
            try:
                self._execute_UPDATE("ratings", ["rating"], [rating_value], "id=?", [id])
            except:
                return False, "Database Failure"

    def update_user_admin_status(self, admin_id, user_id, new_status):
        """

        :param admin_id:            The admin that performs the update
        :param user_id:             The user the update is performed for
        :param new_status:          The new status (has to be either 1/0)

        :return:                    A dictionary with the following format:
                                    {
                                        "success":  <True/False>,
                                        "message":  <ERROR_message> (only if not successful)
                                    }
        """

        if admin_id == user_id:
            return {"success": False, "message": "Can't update your own status!!"}

        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the operation"}

        user = self._get_user_from_hash(user_id)

        if user is None:
            return {"success": False, "message": "Invalid user ID"}

        if user[4] == new_status:
            # Not necessary to perform the actual update
            return {"success": True}

        try:
            self._execute_UPDATE("users", conds="uid=?", conds_args=[user[0]], cols=["admin"], new_values=[new_status])
        except:
            return {"success": False, "message": "Database failure"}

        return {"success": True}

    def add_course_category(self, admin_id, new_category):
        """
            Method that adds a course category

        :param admin_id:            The id of the admin performing the action
        :param new_category:        The name of the new course category

        :return:                    A dictionary of the format:

                                    {
                                        "success": <True/ False>,
                                        "message": <ERROR message>  (only if not successful)
                                    }
        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        try:
            self._execute_INSERT("course_categories", ["category_name"], new_category)
        except:
            return {"success": False, "message": "Database failure"}

        return {"success": True}

    def remove_course_category(self, admin_id, category_name):
        """
            Method that removes a course category from the database.
            It also archives every log entry that has something to do with that course category.
            It also
            *NOTE: *    If a user is working on a course from that category, the DELETE will not happen!!!

        :param admin_id:                The id of the admin performing the action
        :param category_name:           The name of the category that will be removed

        :return:                        A dictionary with the following format:

                                        {
                                            "success":  <True/ False>,
                                            "message":  <ERROR message>     (only if not successful)
                                        }
        """

        if self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        query = "SELECT w.id " \
                "FROM working AS w " \
                    "INNER JOIN courses AS c ON w.cid = c.id " \
                    "INNER JOIN course_categories AS cc ON c.cid = cc.id " \
                "WHERE cc.category_name=? " \
                "LIMIT 1"

        try:
            result = self._execute_SELECT_from_query(query, category_name)
        except:
            return {"success": False, "message": "Database failure"}

        if not len(result) == 0:
            # Someone is working on a course related to this category
            return {"success": False, "message": "ERROR: A user is working on a course from that category"}

        # Otherwise, we can just keep on going with this

        archiver_success = self._create_partial_archive(conds="cc.name=?", value=category_name,
                                                        reason="Removing category from database")

        if not archiver_success:
            return {"success": False, "message": "ERROR while creating the archive"}

        delete_success = self._delete_logs_based_on_category(category_name)

        if not delete_success:
            return {"success": False, "message": "ERROR while deleting the logs"}

        delete_query = "DELETE FROM courses " \
                       "WHERE courses.id IN ( " \
                            "SELECT c.id " \
                                "FROM courses AS c " \
                                "INNER JOIN course_categories AS cc " \
                                    "ON c.cid = cc.id " \
                            "WHERE cc.category_name = ?)"

        try:
            self._execute_query(delete_query, category_name)
        except:
            return {"success": False, "message": "Database failure"}

        try:
            self._execute_DELETE("course_categories", "category_name=?", category_name)
        except:
            return {"success": False, "message": "Database failure"}

        return {"success": True}

    def add_course(self, admin_id, new_course):
        """

        :param admin_id:        The ID of the admin performing the action
        :param new_course:      The data about the course. It has to be a dictionary with the following format:

                                {
                                    "name:"     <course_name>,
                                    "url:"      <course_url>,
                                    "category": <category_name>
                                    "description",                          (optional)
                                    "about",                                (optional)
                                    "syllabus",                             (optional)
                                    "notes",                                (optional)
                                    "weekly_commitment_low",                (optional)
                                    "weekly_commitment_high"                (optional)
                                    "number_weeks"                          (optional)
                                }

        :return:
                                 A dictionary with the following format:

                                {
                                    "success": <True/ False>,
                                    "message": <ERROR message>              (only if not successful)
                                }
        """

        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        columns = new_course.keys()

        values = [new_course[key] for key in new_course.keys()]

        try:
            self._execute_INSERT("courses", cols=columns, *values)
        except:
            return {"success": False, "message": "Database failure"}

        return {"success": True}

    def remove_course(self, admin_id, course_name):
        """
            Method that removes a course from the database
            *Note1:* this only happens if NO USER IS WORKING ON THAT COURSE
            *Note2:* it also archives all the logs that were related to that course

        :param admin_id:            The id of the admin performing the action
        :param course_name:         The name of the course we want to delete

        :return:                    A dictionary with the following format:
                                    {
                                        "success": <True/ False>,
                                        "message": <ERROR message>              (only if not successful)
                                    }
        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        try:
            course = self._execute_SELECT("courses", conds="name=?", args=[course_name])
        except:
            return {"success": False, "message": "Database failure"}

        if len(course) == 0:
            return {"success": False, "message": "Invalid course name"}

        select_query = "SELECT w.id " \
                            "FROM working AS w " \
                            "INNER JOIN courses AS c " \
                                "ON w.cid = c.id " \
                       "WHERE c.name=?"

        try:
            result = self._execute_SELECT_from_query(select_query, course_name)
        except:
            return {"success": False, "message": "Database failure"}

        if not len(result) == 0:
            return {"success": False, "message": "ERROR: User working on the course. Can't archive the logs."}

        archive_success = self._create_partial_archive(conds="c.name=?", value=course_name,
                                                       reason="deleting course from the database")

        if not archive_success:
            return {"success": False, "message": "ERROR while archiving the entries"}

        try:
            self._execute_DELETE("logs", "cid=?", course[0])
        except:
            return {"success": False, "message": "ERROR while deleting old logs"}

        return {"success": True}

    def edit_course(self, admin_id, course_name, new_details):
        """

        :param admin_id:                The id of the admin performing the action
        :param course_name:             The name of the course that is being edited
        :param new_details:             The new details of the course
                                        *Note: * Has to be a dictionary with the following format:
                                        {
                                            "name:"     <course_name>,
                                            "url:"      <course_url>,
                                            "category": <category_name>
                                            "description",                          (optional)
                                            "about",                                (optional)
                                            "syllabus",                             (optional)
                                            "notes",                                (optional)
                                            "weekly_commitment_low",                (optional)
                                            "weekly_commitment_high"                (optional)
                                            "number_weeks"                          (optional)
                                        }

        :return:                        A dictionary with the following format:
                                        {
                                            "success": <True/ False>,
                                            "message": <ERROR message>              (only if not successful)
                                        }

        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        try:
            course_id = self._execute_SELECT(table="courses", conds="name=?", cols=["id"], args=[course_name])
        except:
            return {"success": False, "message": "Database failure"}

        if len(course_id) == 0:
            return {"success": False, "message": "Invalid course name"}

        cid = course_id[0][0]

        try:
            self._execute_UPDATE(table="courses",
                                cols=new_details.keys(),
                                new_values = [new_details[x] for x in new_details.keys()],
                                conds="id=?",
                                conds_args=[cid])
        except:
            return {"success": False, "message": "Database failure"}

        return {"success": True}

    def remove_user(self, admin_id, user_id):
        """
            Method that removes a user from the database
            * Note1: * Before physically removing the user, all the logs related to he/ she are logged
            * Note2: * If the user is currently working, he/ she will NOT be deleted
            * Note3: * admin_id has to be DIFFERENT from user_id

        :param admin_id:            The id of the admin performing the action
        :param user_id:             The id of the user we want to remove

        :return:                    A dictionary witht he following format:
                                    {
                                        "success": <True/ False>
                                        "message": <ERROR message>                  (only if not succcessful)
                                    }
        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action!"}

        if admin_id == user_id:
            return {"success": False, "message": "Cannot remove yourself from the database"}

        user = self._get_user_from_hash(user_id)

        if user is None:
            return {"success": False, "message": "Invalid user id!"}

        uid = user[0]

        try:
            user_working_on = self._execute_SELECT(table="working", conds="uid=?", cols=["id"], limit=1, args=[uid])
        except:
            return {"success": False, "message": "Database failure"}

        if not len(user_working_on) == 0:
            return {"success": False, "message": "User currently working!"}

        archive_success = self._create_partial_archive(conds="u.id=?", value=uid, reason="Removing user from database")

        if not archive_success:
            return {"success": False, "message": "ERROR while archiving user logs"}

        try:
            self._execute_DELETE("logs", "uid=?", uid)
        except:
            return {"success": False, "message": "ERROR while deleting logs"}

        try:
            self._execute_DELETE("users", "id=?", uid)
        except:
            return {"success": False, "message": "ERROR while deleting user from database"}

        return {"success": True}

    def update_category_name(self, admin_id, old_name, new_name):
        """

        :param admin_id:            id of the admin performing the action
        :param old_name:            old name of the category
        :param new_name:            new name of the category

        :return:                    A dictionary with the following format:
                                    {
                                        "success": <True/ False>
                                        "message": <ERROR message>          (only if not successful)
                                    }
        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        try:
            self._execute_UPDATE(table="course_categories",
                                 cols=["name"], new_values=[new_name],
                                 conds="name=?", conds_args=[old_name])
        except:
            return {"success": False, "message": "Database failure"}

        return {"success": True}

    def archive_logs(self, admin_id):
        """
            Method that archives all the logs from the live database

            *Note: *    It also deletes the logs from the live database

        :param admin_id:            id of the admin performing the action

        :return:                    A dictionary of the following format:
                                    {
                                        "success": <True/ False>
                                        "message": <ERROR message>      (only if not successful)
                                    }
        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        select_query = "SELECT u.name, u.email, c.name, c.url, c.description, cc.category_name, l.duration, " \
                                "l.started_at, l.logged_at " \
                            "FROM logs AS l " \
                            "INNER JOIN courses AS c " \
                                "ON l.cid = c.id " \
                            "INNER JOIN course_categories AS cc " \
                                "ON c.cid = cc.id " \
                            "INNER JOIN users AS u " \
                                "ON u.id = l.uid;"

        try:
            partial_data = self._execute_SELECT_from_query(select_query)
        except:
            return {"success": False, "message": "Database failure"}

        archive_success = self._insert_into_archive(partial_data, "Archiving done by admin")

        if not archive_success:
            return {"success": False, "message": "ERROR while inserting data into archive"}

        try:
            self._execute_DELETE(table="logs", conds="1=1")
        except:
            return {"success": False, "message": "ERROR while deleting the logs"}

        return {"success": True}

    def get_logged_in_users(self, admin_id):
        """

        :param admin_id:            The id of the admin performing the action

        :return:                    A dictionary with the following format:
                                    {
                                        "success": <True/ False>,
                                        "users": [                                          (only if successful)
                                            {
                                                "id":  <id of the list entry>,
                                                "name": <name of the user who's logged in>,
                                                "email": <email of the user>
                                                "logged_at:" <date when the user logged in last time>,
                                                "expiry_date": <date when the login token expires>,
                                                "mailto_link": <link for enabling the email to the user>,
                                                "logout_function": <logout function for the logout button>,
                                                "user_details_function": <JS function to get more information about the user>
                                            },
                                            {
                                                ....
                                            }
                                            ...
                                        ],
                                        "message": <ERROR message>                          (only if not successful)
                                    }
        """
        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform the action"}

        query = "SELECT u.full_name, u.email, li.last_login, li.TTL " \
                    "FROM users AS u " \
                    "INNER JOIN logged_in AS li " \
                        "ON u.id = li.uid;" \


        logged_in_users = self._execute_SELECT_from_query(query)


        result = {
            "success": True,
            "users": list()
        }
        id = 1

        for user in logged_in_users:
            new_entry = {
                "id": id,
                "name": user[0],
                "email": user[1],
                "logged_at": user[2],
                "expiry_date": str(dt_parse.parse(user[2]) + datetime.timedelta(seconds=user[3])),
                "mailto_link": "mailto:" + user[1],
                "logout_function": "forced_logout('" + self._get_sha256_encryption(user[1]) + "')",
                "user_details_function": "get_user_details('user', '" + self._get_sha256_encryption(user[1]) + "')"
            }
            result["users"].append(new_entry)
            id += 1

        return result

    def get_full_users_list(self, admin_id):
        """
            Method that gets the full list of users from the database

        :param admin_id:        The id of the admin asking for the list

        :return:                A dictionary of the following format:

                                {
                                    "success":  <True/ False>,
                                    "users": [                                          (only if successful)
                                        {
                                            "id": <id of the entry in the list>,
                                            "name": <user's name>,
                                            "email": <user's email>,
                                            "admin": <Yes/ No> (whether the user is an admin or not)
                                            "mailto_link": <link to enable mailto functionality>,
                                            "more_details_function": <JS function called to get more details on the user>
                                        }
                                        {
                                            ...
                                        }
                                        ...
                                    ],
                                    "message": <ERROR message>                          (only if not successful)
                                }
        """

        if not self.is_admin(admin_id):
            return {"success": False, "message": "Not enough rights to perform this action"}

        try:
            users = self._execute_SELECT(table="users", conds=None)
        except:
            return {"success": False, "message": "Database failure"}

        id = 1
        result = {
            "success":  True,
            "users": list()
        }

        for user in users:
            new_entry = {
                "id": id,
                "name": user[2],
                "email": user[1],
                "mailto_link": "mailto:" + user[1],
                "more_details_function": "get_user_details('" + self._get_sha256_encryption(user[1]) + "')",
                "admin": "Yes" if user[-1] == 1 else "No"
            }
            id += 1
            result["users"].append(new_entry)

        return result
