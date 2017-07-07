import sqlite3 as sql

def _execute_SELECT(db_name, table, conds, cols=["*"], limit=None, order=None, groupBy=None, *args):

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

    con = sql.connect(db_name)
    cur = con.cursor()
    cur.execute(query, args)
    results = list(set(cur.fetchall()))
    con.commit()
    con.close()

    return results

def _execute_INSERT(db_path, table, cols, *args):
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

    _execute_query(db_path,query, *args)


def _execute_query(db_path, query, *args):
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


def migrate_table(old_db, new_db, table_name, first_index):

    query = "pragma table_info(" + table_name + ");"
    con = sql.connect(old_db)
    cur = con.cursor()
    cur.execute(query)
    results = list(set(cur.fetchall()))
    cols_list = [x[1] for x in sorted(results, key=lambda result: result[0])]
    print(cols_list)
    con.commit()
    con.close()

    old_table_data = [x[first_index:] for x in _execute_SELECT(old_db, table_name, None)]

    for tuple in old_table_data:
        _execute_INSERT(new_db, table_name, cols_list, *tuple)


if __name__ == "__main__":

    old_db = input("Old database name: ")
    new_db = input("New database name: ")

    migrate_table(old_db, new_db, "logs", 1)
    migrate_table(old_db, new_db, "working", 0)