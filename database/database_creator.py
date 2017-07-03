import sqlite3 as sql


def execute_query(query, *args):
    """
        Function that executes a given query, except SELECT queries
    :param query:       the query to be executed
    :param args:        the arguments to be inserted
    :return:
    """

    con = sql.connect("tests/SMU-logs.db")
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    con.close()


def create_users_table():
    query = "CREATE TABLE IF NOT EXISTS " \
            "users ( " \
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                "email VARCHAR(254) NOT NULL, " \
                "full_name VARCHAR(100) NOT NULL, " \
                "salt VARCHAR(64) NOT NULL, " \
                "password VARCHAR(64) NOT NULL, " \
                "admin INTEGER NOT NULL DEFAULT 0 " \
            ");"

    execute_query(query)


def create_working_table():
    query = "CREATE TABLE IF NOT EXISTS " \
            "working (" \
                "uid INTEGER PRIMARY KEY, " \
                "working INTEGER NOT NULL DEFAULT 0, " \
                "since DATE, " \
                "cid INTEGER NOT NULL, " \
                "FOREIGN KEY(uid) REFERENCES users(id), " \
                "FOREIGN KEY(cid) REFERENCES courses(id)" \
            ");"

    execute_query(query)


def create_courses_table():
    query = "CREATE TABLE IF NOT EXISTS " \
            "courses (" \
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                "name VARCHAR(100) NOT NULL, " \
                "url VARCHAR(500) NOT NULL," \
                "cid INTEGER NOT NULL, " \
                "description TEXT," \
                "about TEXT, " \
                "syllabus TEXT," \
                "notes TEXT," \
                "weekly_commitment_lower_limit INT NOT NULL," \
                "weekly_commitment_higher_limit INT," \
                "number_weeks INT NOT NULL" \
                "FOREIGN KEY(cid) REFERENCES course_categories(id)" \
            ");"

    execute_query(query)


def create_course_categories_table():
    query = "CREATE TABLE IF NOT EXISTS " \
            "course_categories (" \
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                "category_name VARCHAR(50) NOT NULL" \
            ");"

    execute_query(query)


def create_log_table():
    query = "CREATE TABLE IF NOT EXISTS " \
            "logs (" \
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                "uid INTEGER NOT NULL, " \
                "cid INTEGER NOT NULL, " \
                "duration INTEGER NOT NULL, " \
                "FOREIGN KEY(cid) REFERENCES courses(id), " \
                "FOREIGN KEY(uid) REFERENCES users(id)" \
            ");"

    execute_query(query)

if __name__ == "__main__":
    print("Creating tables...")
    create_users_table()
    print("Created users table!")
    create_working_table()
    print("Created working table!")
    create_course_categories_table()
    print("Created course_categories table!")
    create_courses_table()
    print("Created courses table!")
    create_log_table()
    print("Created logs table!")
    print("Done!")