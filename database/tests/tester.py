from database.database_handler import DatabaseHandler as DH
import sqlite3 as sql

dh = DH("SMU-logs.db")


def _execute_SELECT(table, conds, cols=["*"], limit=None, order=None, groupBy=None, *args):
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

    con = sql.connect("SMU-logs.db")
    cur = con.cursor()
    cur.execute(query, args)
    results = list(set(cur.fetchall()))
    con.commit()
    con.close()

    return results


def _execute_query(query, *args):
    """
        Function that executes a given query, except SELECT queries
    :param query:       the query to be executed
    :param args:        the arguments to be inserted
    :return:
    """

    con = sql.connect("SMU-logs.db")
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    con.close()


def _execute_INSERT(table, cols, *args):
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

    _execute_query(query, *args)


def insert_mock_data():
    print("Inserting mock data...")
    _execute_INSERT("users",
                    ["email", "full_name", "salt", "password", "admin"],
                    "test@test.test", "Mr Test", "blah", "blah", 1)

    _execute_INSERT("users",
                    ["email", "full_name", "salt", "password", "admin"],
                    "test1@test1.test", "Mr Test1", "blah", "blah", 0)

    _execute_INSERT("users",
                    ["email", "full_name", "salt", "password", "admin"],
                    "testing@test1.test", "Mr Test1000", "blah", "blah", 0)

    print("Inserted 3 users")

    _execute_INSERT("course_categories",
                    ["category_name"],
                    "category test 1")

    _execute_INSERT("course_categories",
                    ["category_name"],
                    "category test 2")

    print("Inserted 2 course categories")

    _execute_INSERT("courses",
                    ["name", "url", "cid"],
                    "Course1", "www.course1.test", 1)

    _execute_INSERT("courses",
                    ["name", "url", "cid"],
                    "Course2", "www.course2.test", 2)

    _execute_INSERT("courses",
                    ["name", "url", "cid"],
                    "Course3", "www.course3.test", 1)

    _execute_INSERT("courses",
                    ["name", "url", "cid"],
                    "Course4", "www.course4.test", 1)

    print("Inserted 4 courses")

    print("Done inserting mock data")


def test_insertions():
    print("Starting SELECT tests...")

    print("Users table:")
    print(_execute_SELECT("users", None))
    print("\n")

    print("Courses table:")
    print(_execute_SELECT("courses", None))
    print("\n")

    print("Course Categories table:")
    print(_execute_SELECT("course_categories", None))
    print("\n")

    print("Finished testing SELECT")


def test_handler_basic():

    print("\nStarting basic handler testing...")

    print("Testing start_work")

    print(dh.start_work("test@test.com", "Course3"))

    print(dh.start_work("test@test.test", "Course10"))
    print(dh.start_work("test@test.test", "Course2"))
    print(dh.start_work("test@test.test", "Course1"))

    print("DONE")

    print(_execute_SELECT("working", None))




if __name__ == "__main__":
    insert_mock_data()
    test_insertions()
    test_handler_basic()
