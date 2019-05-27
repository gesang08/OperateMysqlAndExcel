# Operate MySQL DB and excel
The program for the following：
#!/usr/bin/env python
# _*_ coding: UTF-8 _*_

"""
实现操作数据库的类，可将从数据库获得的以字段为键，以字段内容为值的存储格式数据；
实现对excel表的创建，读取，写入，追加的类
"""

import MySQLdb
import MySQLdb.cursors
import os
import xlwt
import xlrd
import xlutils.copy  # xlutils 读入一个excel文件，然后进行修改或追加，不能操作xlsx，只能操作xls

SERVER_IP = '127.0.0.1'
USER = 'root'
PASSWORD = '12345678'
DB = 'gs_package'
PORT = 3306
CHARSET = 'utf8'


def main():
    sql = "SELECT `Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, `Door_thick`, `Package_state`, `Element_type_id` FROM `order_part_online` WHERE 1"
    db = database()
    ex = operate_excel(excel_file_name='data.xls')
    q = db.get_more_row(sql)
    # ex.write_excel(q)
    print ex.read_excel()
    # ex.append_excel()
    # for i in range(len(q)):
    #     print q


class database(object):
    """
    封装数据库操作类
    """
    # 注，python的self等于其它语言的this
    def __init__(self, log=None, dbhost=None, dbname=None, user=None, password=None, port=None, charset=None):
        self._logger = log
        # 这里的None相当于其它语言的NULL
        self._dbhost = SERVER_IP if dbhost is None else dbhost
        self._dbname = DB if dbname is None else dbname
        self._user = USER if user is None else user
        self._password = PASSWORD if password is None else password
        self._port = PORT if port is None else port
        self._charset = CHARSET if charset is None else charset
        self.conn = None
        self.get_conn_result = self.is_connection_db()
        if self.get_conn_result:  # 只有数据库连接上才获取数据游标
            self._cursor = self.conn.cursor()

    def is_connection_db(self, get_data_method='dict'):
        """
        数据库连接方法，默认获取的数据类型为字典，它以字段为key，以字段下的数据为value
        :param get_data_method:
        :return:
        """
        try:
            if get_data_method == 'dict':
                # 1.获取一行数据，返回的是dict类型，它以数据表中的字段为key，以字段下的数据为value
                # 2.获取多行数据，返回的是tuple类型，tuple序列内容为dict类型，它以数据表中的字段为key，以字段下的数据为value
                self.conn = MySQLdb.connect(host=self._dbhost,
                                            user=self._user,
                                            passwd=self._password,
                                            db=self._dbname,
                                            port=self._port,
                                            cursorclass=MySQLdb.cursors.DictCursor,
                                            charset=self._charset,
                                            )
            elif get_data_method == 'tuple':
                self.conn = MySQLdb.connect(host=self._dbhost,
                                            user=self._user,
                                            passwd=self._password,
                                            db=self._dbname,
                                            port=self._port,
                                            charset=self._charset,
                                            )
            else:
                self._logger.warn("please give correct method for getting data!")
                return False
        except Exception, e:
            self._logger.warn("query database exception,%s" % e)
            return False
        else:
            return True

    def get_more_row(self, sql):
        """
        从数据库中获取多行数据方法
        :param sql:
        :return:
        """
        record = ""
        if self.get_conn_result:
            try:
                self._cursor.execute(sql)
                record = self._cursor.fetchall()  # 获取多行数据函数
                if record == () or record is None:
                    record = False
                self._cursor.close()  # 关闭游标
                self.conn.close()  # 关闭数据库
            except Exception, e:
                record = False
                self._logger.warn("query database exception,sql= %s,%s" % (sql, e))
        return record

    def get_one_row(self, sql):
        """
        从数据库中获取一行数据方法
        :param sql:
        :return:
        """
        record = ""
        if self.get_conn_result:
            try:
                self._cursor.execute(sql)
                record = self._cursor.fetchone()  # 获取多行数据函数
                if record == () or record is None:
                    record = False
                self._cursor.close()  # 关闭游标
                self.conn.close()  # 关闭数据库
            except Exception, e:
                record = False
                self._logger.warn("query database exception,sql= %s,%s" % (sql, e))
        return record

    def modify_sql(self, sql):
        """
        更新、插入、删除数据库数据方法
        :param sql:
        :return:
        """
        flag = False
        if self.get_conn_result:
            try:
                self._cursor.execute(sql)
                self.conn.commit()
                flag = True
            except Exception, e:
                flag = False
                self._logger.warn("query database exception,sql= %s,%s" % (sql, e))
        return flag


'''
常用’/‘来表示相对路径，’\‘来表示绝对路径，还有路径里\\是转义的意思（python3也可以写成open(r'D:\user\ccc.txt')，r表示转义）
'''
class operate_excel(object):
    """
    创建excel表，并操作excel表的读写，保存表
    """
    def __init__(self, log=None, excel_file_name=None, sheet_name="sqldata"):
        self._logger = log
        self.excel_file_name = excel_file_name
        self.sheet_name = sheet_name

    def create_excel(self):
        all_files = os.listdir(os.getcwd())  # 获取当前工程项目文件夹下所有文件名
        if self.excel_file_name not in all_files:
            excel_file = open(self.excel_file_name, 'w+')
            excel_file.close()
            self.excel_file_name = excel_file.name

    def write_excel(self, data):
        """
        将数据库数据写到excel中
        :param data:
        :return:
        """
        i = 0
        key = []
        value = []
        key_2D = []
        value_2D = []
        workbook = xlwt.Workbook(encoding='utf-8')  # 实例化新建工作薄excel的类
        """
        xlwt.Workbook类的构造函数__init__(self,encoding ='ascii',style_compression = 0)
        1.encoding表示文件（.xls or .xlsx）编码格式，一般要这样设置：w = Workbook(encoding='utf-8')，就可以在excel中输出中文了；
        2.style_compression表示是否压缩 ，一般情况下使用默认参数即可
        """
        sheet = workbook.add_sheet(sheetname=self.sheet_name, cell_overwrite_ok=True)  # 新建一个名为self.sheet_name的表
        """
        Workbook类下面的add_sheet(self, sheetname, cell_overwrite_ok=False)方法：
        1.sheetname新增表的名称；
        2.cell_overwrite_ok，表示是否可以覆盖单元格，其实是Worksheet实例化的一个参数，默认值是False，表示不可以覆盖单元格
        """
        if data:
            if isinstance(data, dict):  # 只有一行数据
                for k, v in data.items():
                    key.append(k)
                    value.append(v)
                for k in range(len(key)):
                    sheet.write(i, k, key[k])
                    """
                    xlwt.Worksheet类下面的write(self, r, c, label="", style=Style.default_style)方法：
                    1.r:行的数字编号index，从0开始
                    2.c:列的数字编号index，从0开始
                    3.label：要写入的数据值
                    4.style：样式（也称为XF（扩展格式））是一个 XFStyle对象，它封装应用于单元格及其内容的格式。
                        XFStyle最好使用该easyxf()功能设置对象 。它们也可以通过在设置属性设置Alignment，Borders， Pattern，
                        Font和Protection对象然后设置这些对象和一个格式字符串作为属性 XFStyle对象。
                    """
                i += 1
                for k in range(len(value)):
                    sheet.write(i, k, value[k])
            if isinstance(data, tuple):  # 有多行数据
                for data_row in data:
                    for k, v in data_row.items():
                        key.append(k)
                        value.append(v)
                    key_2D.append(key)
                    value_2D.append(value)
                    key = []
                    value = []
                for k in range(len(key_2D[0])):
                    sheet.write(i, k, key_2D[0][k])
                i += 1
                for row in range(len(value_2D)):
                    for col in range(len(value_2D[row])):
                        sheet.write(row + 1, col, value_2D[row][col])
        workbook.save('./%s' % self.excel_file_name)
        """
        Workbook类下面的save(self, filename_or_stream)方法：
        filename_or_stream：1.这可以是包含文件文件名的字符串，在这种情况下，使用提供的名称将excel文件保存到磁盘。
        2.它也可以是具有write方法的流对象，例如a StringIO，在这种情况下，excel文件的数据被写入流。
        若./的相对路径下没有self.excel_file_name文件，则创建self.excel_file_name的文件进行保存
        """

    def read_excel(self):
        content = []
        data = xlrd.open_workbook('./%s' % self.excel_file_name)
        table = data.sheets()[0]  # 通过索引顺序获取表
        # table = data.sheet_by_index(0)  # 通过索引顺序获取表
        # table = data.sheet_by_name(self.sheet_name)  # 通过名称获取表
        """
        通过行table.nrows（获取行数）和table.row_values(i)（获取整行数据，以list形式返回）获得excel数据
        """
        for i in range(table.nrows):
            content.append(table.row_values(i))
        """
        通过列table.ncols（获取列数）和table.col_values(i)（获取整列数据，以list形式返回）获得excel数据
        """
        # for i in range(table.ncols):
        #     content.append(table.col_values(i))
        """
        通过table.cell_value(i, j)（获取单元格数据）获得excel数据
        """
        # for i in range(table.nrows):
        #     for j in range(table.ncols):
        #         content.append(table.cell_value(i, j))
        # B1 = table.row(0)[1].value  # 通过行列索引来获取单元格数据
        return content

    def append_excel(self):
        data = xlrd.open_workbook('./%s' % self.excel_file_name)
        buffer_data = xlutils.copy.copy(data)
        table = buffer_data.get_sheet(0)
        table.write(90, 0, 'append_test')
        buffer_data.save('./%s' % self.excel_file_name)


if __name__ == '__main__':
    main()
