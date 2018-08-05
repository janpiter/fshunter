import MySQLdb

__author__ = 'irvan'


def x_str(s):
    return '' if s is None else str(s)


class Db:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor
        self.q_update_set = None
        self.q_select = None
        self.q_where = None
        self.q_join = None
        self.q_order = None
        self.sql = None
        self.sql_insert = None
        self.sql_delete = None
        self.delete_all = None
        self.sql_update = None
        self.q_group_by = None
        self.q_limit = None

    def reset_var(self):
        dic = vars(self)
        var_exceptions = ['conn', 'cursor']
        for i in dic.keys():
            if i not in var_exceptions:
                dic[i] = None

    def select(self, table, alias=None, field="*"):
        field = "SQL_CALC_FOUND_ROWS {}".format(field)
        if isinstance(field, list):
            field = ", ".join(field)
        if alias is None:
            alias = table
        self.q_select = "SELECT {} FROM {} {}".format(field, table, alias)

    def join(self, table, alias, using=None, on=None, join_type=''):
        condition = ''
        if using:
            condition = "USING({})".format(using)
        elif on:
            condition = "ON {}".format(on)
        if join_type.upper() not in ['LEFT', 'RIGHT', 'INNER']:
            join_type = ''
        q_join = "{} JOIN {} {} {}".format(join_type.upper(), table, alias, condition)
        if self.q_join:
            self.q_join = "{} {}".format(self.q_join, q_join)
        else:
            self.q_join = q_join

    def order(self, by=None, reverse=False, random=False):
        q_order = None
        order_type = "ASC"
        if reverse:
            order_type = "DESC"
        if random:
            q_order = 'RAND()'
        elif by:
            q_order = '{} {}'.format(by, order_type)

        if self.q_order:
            self.q_order = '{}, {}'.format(self.q_order, q_order)
        else:
            self.q_order = "ORDER BY {}".format(q_order)

    def order_by(self, order_by):
        self.q_order = "ORDER BY {}".format(order_by)

    def limit(self, offset=None, limit=None):
        if offset and limit:
            self.q_limit = "LIMIT {}, {}".format(offset, limit)
        elif limit:
            self.q_limit = "LIMIT {}".format(limit)

    def where(self, condition, operator='AND'):
        if isinstance(condition, list):
            pass
        if self.q_where:
            self.q_where = "{} {} {}".format(self.q_where, operator, condition)
        else:
            self.q_where = '{}'.format(condition)

    def exact_where(self, column, value, operator='AND'):
        if value is not None or value == 0:
            value = str(value)
        if column and value:
            self.where("{} = '{}'".format(column,
                                          MySQLdb.escape_string(str(value))),
                       operator)

    def group_by(self, field):
        self.q_group_by = "GROUP BY {}".format(field)

    def insert(self, table, data, is_ignore=None, is_update_field_id=None):
        update_field = []
        if isinstance(data, dict):
            fields = []
            values = []
            for d in data:
                # noinspection PyBroadException
                try:
                    data[d] = data[d].encode('utf-8')
                except Exception:
                    pass

                fields.append(d)
                values.append('NULL' if data[d] is None
                              else MySQLdb.escape_string(str(data[d])))
                if is_update_field_id:
                    if d not in is_update_field_id and d not in update_field:
                        update_field.append(d)

            if is_ignore:
                self.sql_insert = """INSERT IGNORE INTO {}({}) 
                                     VALUES ('{}')""".format(table,
                                                             ", ".join(fields),
                                                             "', '".join(values))
            elif is_update_field_id:
                on_duplicate = ["{0} = VALUES({0})".format(uf) for uf in update_field]
                self.sql_insert = """INSERT INTO {}({}) 
                                     VALUES ('{}') 
                                     ON DUPLICATE KEY UPDATE {}""".format(table,
                                                                          ", ".join(fields),
                                                                          "', '".join(values),
                                                                          ", ".join(on_duplicate))
            else:
                self.sql_insert = """INSERT INTO {}({}) 
                                     VALUES ('{}')""".format(table,
                                                             ", ".join(fields),
                                                             "', '".join(values))
        elif isinstance(data, list):
            fields = []
            values = []
            for dat in data:
                if not fields:
                    for d in dat:
                        fields.append(d)
                value = []
                for field in fields:
                    # noinspection PyBroadException
                    try:
                        dat[field] = dat[field].encode('utf-8')
                    except Exception:
                        pass
                    value.append('NULL' if dat[field] is None
                                 else MySQLdb.escape_string(str(dat[field])))
                    if is_update_field_id:
                        if field not in is_update_field_id and field not in update_field:
                            update_field.append(field)
                values.append("('{}')".format("', '".join(value)))
            if is_ignore:
                self.sql_insert = """INSERT IGNORE INTO {}({}) 
                                     VALUES {}""".format(table,
                                                         ", ".join(fields),
                                                         ", ".join(values))
            elif is_update_field_id:
                on_duplicate = ["{0} = VALUES({0})".format(uf) for uf in update_field]
                self.sql_insert = """INSERT INTO {}({}) 
                                     VALUES {} 
                                     ON DUPLICATE KEY UPDATE {}""".format(table,
                                                                          ", ".join(fields),
                                                                          ", ".join(values),
                                                                          ", ".join(on_duplicate))
            else:
                self.sql_insert = """INSERT INTO {}({}) 
                                     VALUES {}""".format(table,
                                                         ", ".join(fields),
                                                         ", ".join(values))

    def delete(self, table, delete_all=False):
        self.sql_delete = "DELETE FROM {}".format(table)
        if delete_all is True:
            self.delete_all = True

    def update(self, table, data=None):
        if data:
            for column, value in data.iteritems():
                self.update_set(column, value)
        self.sql_update = "UPDATE {}".format(table)

    def update_set(self, column, value, inc=None):
        if not self.q_update_set:
            self.q_update_set = list()

        if column and value:  # while value is null
            if isinstance(value, str):
                value = MySQLdb.escape_string(value)

            if inc is None:
                if value == 'null':
                    self.q_update_set.append("{} = NULL".format(column))
                else:
                    self.q_update_set.append("{} = '{}'".format(column, value))
            elif inc is False:
                self.q_update_set.append("{0} = {0} - {1}".format(column, value))
            else:
                self.q_update_set.append("{0} = {0} + {1}".format(column, value))

    def query(self, sql):
        self.sql = sql

    def execute(self, commit=True, utf8mb64=False, debug=False):
        if self.q_where and self.q_where != '':
            self.q_where = "WHERE {}".format(self.q_where)
        if self.sql_insert:
            sql = self.sql_insert.replace("'NULL'", 'NULL')
        elif self.sql_delete and self.q_where:
            sql = "{} {}".format(self.sql_delete, self.q_where)
        elif self.sql_delete and self.sql_delete:
            sql = self.sql_delete
        elif self.sql_update and self.q_where:
            set_clause = ", ".join(self.q_update_set)
            sql = "{} SET {} {}".format(self.sql_update, set_clause, self.q_where)
        elif self.sql:
            sql = self.sql
        else:
            sql = "{} {} {} {} {} {}".format(x_str(self.q_select),
                                             x_str(self.q_join),
                                             x_str(self.q_where),
                                             x_str(self.q_group_by),
                                             x_str(self.q_order),
                                             x_str(self.q_limit))
        if utf8mb64:
            self.cursor.execute('SET NAMES utf8mb4')
            self.cursor.execute("SET CHARACTER SET utf8mb4")
            self.cursor.execute("SET character_set_connection=utf8mb4")

        if debug:
            print sql

        status = self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        self.cursor.execute('SELECT FOUND_ROWS() AS rowscount')
        rowscount = self.cursor.fetchone()['rowscount']
        lastrowid = self.cursor.lastrowid
        if commit:
            self.conn.commit()

        self.reset_var()

        return Return(sql=sql, rows=rows, rowscount=rowscount,
                      status=status, lastrowid=lastrowid)


class Return:
    def __init__(self, sql, rows, rowscount=0, status=0, lastrowid=None):
        self.status = status
        self.sql = sql
        self.data = rows
        self.rowscount = rowscount
        self.fetchall = rows
        self.fetchone = dict()
        self.lastrowid = lastrowid
        if rows:
            self.fetchone = rows[0]
