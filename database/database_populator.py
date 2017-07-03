import pandas as pd
import sqlite3 as sql

db_path = ""

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

    _execute_query(query, *args)


def _execute_query(query, *args):
    """
        Function that executes a given query, except SELECT queries
    :param query:       the query to be executed
    :param args:        the arguments to be inserted
    :return:
    """

    con = sql.connect(db_path)
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    con.close()


def populate_categories():
    print("Populating categories table ...")
    categories_list = []
    with open("data/categories.txt", "r") as f:
        categories_list = f.read().split("\n")

    for category in categories_list:
        if category != "":
            _execute_INSERT("course_categories", ["category_name"], category)

    print("DONE!")
    return categories_list


def populate_courses(categories_list):
    print("\n")
    print("Populating courses table ...")
    for category in categories_list:
        path = "data/courses/"+category+".csv"
        print(category)
        print(path)
        df = pd.read_csv(path)
        print(df["Link"])

if __name__ == "__main__":
    db_path = input("Enter the database path: ")
    categories_list = populate_categories()
    populate_courses(categories_list)