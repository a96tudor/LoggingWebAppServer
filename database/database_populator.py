import pandas as pd
import sqlite3 as sql
import numpy as np

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
    print()
    print("Populating courses table ...")
    for category in categories_list:
        path = "data/courses/"+category+".csv"
        df = pd.read_csv(path)
        cols = {
            "name": "Name of resource",
            "url": "Link",
            "description": "Description",
            "about": "About",
            "syllabus": "Syllabus",
            "notes": "Notes",
            "weekly_commitment_low": "Weekly time commitment-low(hours)",
            "weekly_commitment_high": "Weekly time commitment-high(hours)",
            "number_weeks": "Length of course(weeks)"
        }
        for idx in df.index.values:
            good_cols_names = ["cid"]
            good_cols_values = [categories_list.index(category) + 1]
            for col in cols:
                if df.loc[idx, cols[col]] != np.nan and not isinstance(df.loc[idx, cols[col]], np.float64):
                    good_cols_names.append(col)
                    if col in ["weekly_commitment_low", "weekly_commitment_high", "number_weeks"]:
                        good_cols_values.append(int(df.loc[idx, cols[col]]))
                    else:
                        good_cols_values.append(df.loc[idx, cols[col]])
            _execute_INSERT("courses", good_cols_names, *good_cols_values)

    print("DONE!")


def populate_users():
    print()
    print("Inserting users...")
    df = pd.read_csv("data/users.csv")
    for idx in df.index.values:
        _execute_INSERT("users", ["full_name", "email"], df.loc[idx, "Name"], df.loc[idx, "Email"])
    print("Done")
    print()
    print("Inserting admins...")
    df = pd.read_csv("data/admins.csv")
    for idx in df.index.values:
        _execute_INSERT("users", ["full_name", "email", "admin"], df.loc[idx, "Name"], df.loc[idx, "Email"], 1)

    print("Done")


def populate_all(path):
    db_path = path
    categories_list = populate_categories()
    populate_courses(categories_list)
    populate_users()

if __name__ == "__main__":
    db_path = input("Enter the database path: ")
    populate_all(db_path)
    #print(_execute_SELECT("users", None))



