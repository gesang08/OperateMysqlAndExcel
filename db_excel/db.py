#!/usr/bin/env python
# _*_ coding: UTF-8 _*_

import time
import MySQLdb
import MySQLdb.cursors
from ID_DEFINE import *
import MySQLdb
from DBUtils.PooledDB import PooledDB
DBNAME = database[0]
DBHOST = server_ip
DBUSER = user_list[0]
DBPWD = password
DBCHARSET = charset
DBPORT = 3306


# 数据库操作类
class database:
    # 注，python的self等于其它语言的this
    def __init__(self, log=None,dbname=None, dbhost=None):
        self._logger = log
        # 这里的None相当于其它语言的NULL
        if dbname is None:
            self._dbname = DBNAME
        else:
            self._dbname = dbname
        if dbhost is None:
            self._dbhost = DBHOST
        else:
            self._dbhost = dbhost

        self._dbuser = DBUSER
        self._dbpassword = DBPWD
        self._dbcharset = DBCHARSET
        self._dbport = int(DBPORT)
        self._conn = self.connectMySQL()  # 判断是否连接

        if (self._conn):
            self._cursor = self._conn.cursor()

    def Is_Database_Connected(self):
        if (self._conn.ping()):
            return True
        else:
            return False

    # 数据库连接
    def connectMySQL(self):
        conn = False
        try:
            conn = MySQLdb.connect(host=self._dbhost,
                                   user=self._dbuser,
                                   passwd=self._dbpassword,
                                   db=self._dbname,
                                   port=self._dbport,
                                   cursorclass=MySQLdb.cursors.DictCursor,
                                   charset=self._dbcharset,
                                   )


        except Exception, data:
            self._logger.warn("query database exception,%s" % ( data))
            conn = False
        return conn

    # 获取查询结果集
    def do_sql(self, sql):
        res = ''
        if self._conn:
            try:
                self._cursor.execute(sql)
                res = self._cursor.fetchall()
                self._conn.commit()

            except Exception, data:
                res = False
                self._logger.warn("query database exception,sql= %s,%s" % (sql, data))
        return res

        # 获取查询结果集

    def do_sql_one(self, sql):
        res = ''

        if (self._conn):
            try:
                self._cursor.execute(sql)
                res = self._cursor.fetchone()
                self._conn.commit()
            except Exception, data:
                res = False
                self._logger.warn("query database exception,sql= %s,%s" % (sql, data))
        return res

    def upda_sql(self, sql):
        flag = False
        if (self._conn):
            try:
                self._cursor.execute(sql)
                self._conn.commit()
                flag = True
            except Exception, data:
                flag = False
                self._logger.warn("query database exception,sql= %s,%s" % (sql, data))
        return flag

    # 关闭数据库连接
    def close(self):
        if (self._conn):

            try:
                self._conn.close()
                if (type(self._cursor) == 'object'):
                    self._cursor.close()
                if (type(self._conn) == 'object'):
                    print "close"
                    self._conn.close()
            except Exception, data:
                self._logger.warn("close database exception, %s,%s,%s" % (data, type(self._cursor), type(self._conn)))
class HCJ_MySQL:
    pool = None
    limit_count = 3  # 最低预启动数据库连接数量

    def __init__(self,log=None,dbname=None,dbhost=None):
        if dbname is None:
            self._dbname = DBNAME
        else:
            self._dbname = dbname
        if dbhost is None:
            self._dbhost = DBHOST
        else:
            self._dbhost = dbhost

        self._dbuser = DBUSER
        self._dbpassword = DBPWD
        self._dbcharset = DBCHARSET
        self._dbport = int(DBPORT)
        self.pool = PooledDB(MySQLdb, self.limit_count, host=self._dbhost, user=self._dbuser, passwd=self._dbpassword, db=self._dbname,
                             port=self._dbport, charset=self._dbcharset, use_unicode=True)
        self._logger = log
    def do_sql(self, sql):
        res = ''
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            res = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception, data:
            res=False
            if self._logger!=None:
                self._logger.warn("query database exception,sql= %s,%s" % (sql, data))
            else:
                print "query database exception,sql= %s,%s" % (sql, data)
        return res
    def do_sql_one(self, sql):
        res = ''
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            res = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception, data:
            res=False
            if self._logger!=None:
                self._logger.warn("query database exception,sql= %s,%s" % (sql, data))
            else:
                print "query database exception,sql= %s,%s" % (sql, data)
        return res
    def upda_sql(self, sql):
        res = ''
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception, data:
            res=False
            if self._logger!=None:
                self._logger.warn("query database exception,sql= %s,%s" % (sql, data))
            else:
                print "query database exception,sql= %s,%s" % (sql, data)
        return res

    def insert(self, table, sql):
        conn = self.pool.connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            conn.commit()
            return {'result': True, 'id': int(cursor.lastrowid)}
        except Exception as err:
            conn.rollback()
            return {'result': False, 'err': err}
        finally:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # sql = "SELECT `Id`,`heterotype`,`Contract_id`,`First_day`,`Element_type_id`,`Board_type`,`Bar_type`,`Double_color`,`Archaize`,`State`,`Order_id`,`Sec_id`,`Time_schedule`,`Board_thick`,`Part_id`,`Code`,`Machining_operator_id`,`Start_Machining_Time`,`Drilling_operator_id`,`Drilling_begin_time`,`Edge_milling_operator_id`,`Edge_milling_begin_time`,`Polish_operator_id`,`Polish_begin_time`,`Regula_operator_id`,`Regula_begin_time`,`Artificial_polishing_operator_id`,`Artificial_polishing_begin_time`,`Half_test_operator_id`,`Half_test_begin_time`,`Sort_before_membrane_operator_id`,`Sort_before_membrane_begin_time`,`Glue_spray_operator_id`,`Glue_spray_begin_time`,`Membrane_operator_id`,`Membrane_begin_time`,`First_quality_inspection_operator_id`,`First_quality_inspection_begin_time`,`Assemble_operator_id`,`Assemble_begin_time`,`Archaize_operator_id`,`Archaize_begin_time`,`Quality_testing_operator_id`,`Quality_testing_begin_time`,`Shelf_after_membrane_operator_id`,`Shelf_after_membrane_time`,`Package_operator_id`,`Package_begin_time`,`Hard_package_operator_id`,`Hard_package_begin_time`,`Shelf_after_package_operator_id`,`Shelf_after_package_begin_time`,`Delievery_schedule_operator_id`,`Delievery_schedule_time`,`Deliver_operator_id`,`Deliver_begin_time`,`Index` FROM `order_element_online` WHERE 1 "
    sql="SELECT `Id`,`heterotype`,`Contract_id`,`First_day`,`Element_type_id`,`Board_type`,`Bar_type`,`Double_color`,`Archaize`,`State`,`Order_id`,`Sec_id`,`Time_schedule`,`Board_thick`,`Part_id`,`Code`,`Machining_operator_id`,`Start_Machining_Time`,`Drilling_operator_id`,`Drilling_begin_time`,`Edge_milling_operator_id`,`Edge_milling_begin_time`,`Polish_operator_id`,`Polish_begin_time`,`Regula_operator_id`,`Regula_begin_time`,`Artificial_polishing_operator_id`,`Artificial_polishing_begin_time`,`Half_test_operator_id`,`Half_test_begin_time`,`Sort_before_membrane_operator_id`,`Sort_before_membrane_begin_time`,`Glue_spray_operator_id`,`Glue_spray_begin_time`,`Membrane_operator_id`,`Membrane_begin_time`,`First_quality_inspection_operator_id`,`First_quality_inspection_begin_time`,`Assemble_operator_id`,`Assemble_begin_time`,`Archaize_operator_id`,`Archaize_begin_time`,`Quality_testing_operator_id`,`Quality_testing_begin_time`,`Shelf_after_membrane_operator_id`,`Shelf_after_membrane_time`,`Package_operator_id`,`Package_begin_time`,`Hard_package_operator_id`,`Hard_package_begin_time`,`Shelf_after_package_operator_id`,`Shelf_after_package_begin_time`,`Delievery_schedule_operator_id`,`Delievery_schedule_time`,`Deliver_operator_id`,`Deliver_begin_time`,`Index` FROM `order_element_online` WHERE `Index` between '619' and '622' and `State`!='1010' "
    timee = time.time()
    db = database()

    print time.time() - timee
    for t in range(5):
        timee=time.time()
        row = db.do_sql(sql)
        # print row
        print time.time()-timee
