#!/usr/bin/env python
# _*_ coding: UTF-8 _*_

# *****************************************************说明*************************************************************
# V20190225a:实现产生门板长宽高及门型参数自动随机生成的类的程序编写与调试
# V20190225b:实现通过点击界面按钮，将随机生成的门板长宽高及门型显示到多行文本中
# V20190228a:完成合同，订单，组件，部件类的编写，但该类下的方法是关联的，不是独立的
#            完成输入框的各种不合理输入的处理
#            实现具有A,B,C,D类数据特征的生成问题，但有限制；实现多订单，多组件，多部件数据生成问题
# V20190228b:将数据类型A，B，C，D类数据特征的生成问题删除，加入高宽在30~2436任意范围的输入
# V20190301a:加入随机same_size的函数，产生订单下部件尺寸相同的门板；加入部件所属组件号与订单号
#            已实现数据生成系统功能，但具有如下缺陷：1.same_size的函数产生的相同尺寸部件数只能为1与质数，不能为4,6等(解决)；
#            2.一个订单下多个组件的话，每个组件数下面的门板数都是相同的；
# V20190308a:1.合同id以合同表单的主键进行编号；2.将生成的数据存到数据库；3.加入正则表达式判断高宽范围输入是否合理；
#            4.加入isdigit()方法判断订单数，组件数，部件数是否合理的为整数
# V20190316a:将产生的部件信息存储到零件表单，此处零件与部件是等同的
# **********************************************************************************************************************

import wx
import wx.lib.mixins.inspection
import random  # 产生随机数的模块
import MySQLdb
import math
import time
import re
from win32api import GetSystemMetrics  # 获取电脑屏幕分辨率大小的模块,使用的是pip install pypiwin32
import sys
reload(sys)
sys.setdefaultencoding('utf8')

SERVER_IP = '127.0.0.1'
USER = 'root'
PASSWORD = '12345678'
DB = 'gs_package'
PORT = 3306
CHARSET = 'utf8'

HeightOrWidthMax = 2436  # 门板高宽上限
HeightOrWidthMin = 30  # 门板高宽下限
HeightAndWidthLimit = 1200  # 门板高宽不能同时大于1200限制


def main():
    app = MyApp()
    app.MainLoop()


def is_connection_db():
    """
    是否成功连接数据库方法
    :return: 成功为True,否则为False
    """
    try:
        global db
        db = MySQLdb.connect(host=SERVER_IP, user=USER, passwd=PASSWORD, db=DB, port=PORT, charset=CHARSET)
    except Exception:
        print u"数据库连接失败!"
        return False
    else:
        return True


class MyApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        mainframe = MyFrame(parent=None, id=wx.ID_ANY, title="数据生成器V20190401a", pos=wx.DefaultPosition, size=(1200,800),
                                style=wx.DEFAULT_FRAME_STYLE)
        mainframe.Center(dir=wx.BOTH)
        mainframe.Show()
        self.SetTopWindow(mainframe)
        return True


class MyFrame(wx.Frame):
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self.panel = wx.Panel(self, -1, size=(1200, 800))
        self.create_button()
        self.create_textctr()
        self.order_input_flag = True
        self.section_input_flag = True
        self.part_input_flag = True
        self.range_input_flag = True

    def create_button(self):
        self.CreateButton = wx.Button(self.panel, -1, "生成", pos=(200, 680))
        self.RemoveButton = wx.Button(self.panel, -1, "清空", pos=(600, 680))
        self.CancelButton = wx.Button(self.panel, -1, "退出", pos=(1000, 680))
        self.CreateButton.Bind(wx.EVT_BUTTON, self.create_data)
        self.RemoveButton.Bind(wx.EVT_BUTTON, self.remove_data)
        self.CancelButton.Bind(wx.EVT_BUTTON, self.cancel)

    def create_textctr(self):
        self.DataText = wx.TextCtrl(self.panel, -1, pos=(0, 200), size=(1180, 400),
                                    style=wx.NO_BORDER | wx.TE_READONLY | wx.TE_MULTILINE | wx.VERTICAL)
        self.OrderAmountLabel = wx.StaticText(self.panel, -1, label="订单数:", pos=(5, 50))
        self.OrderAmountText = wx.TextCtrl(self.panel, -1, pos=(50, 50),)
        self.SectionAmountLabel = wx.StaticText(self.panel, -1, label="组件数:", pos=(5, 100))
        self.SectionAmountText = wx.TextCtrl(self.panel, -1, pos=(50, 100))
        self.PartAmountLabel = wx.StaticText(self.panel, -1, label="部件数:", pos=(5, 150))
        self.PartAmountText = wx.TextCtrl(self.panel, -1, pos=(50, 150))
        # self.DataTypeLabel = wx.StaticText(self.panel, -1, label="数据类型:", pos=(180, 50))
        # self.DataTypeCombobox = wx.ComboBox(self.panel, -1, value='A类', pos=(250, 50), size=(100, 50),
        #                                     choices=['A类', 'B类', 'C类', 'D类'])
        self.HeightLabel = wx.StaticText(self.panel, -1, label="高度范围:", pos=(180, 50))
        self.HeightMinText = wx.TextCtrl(self.panel, -1, pos=(240, 50), size=(50, 22))
        self.SymLabel1 = wx.StaticText(self.panel, -1, label="~", pos=(300, 50))
        self.HeightMaxText = wx.TextCtrl(self.panel, -1, pos=(320, 50), size=(50, 22))
        self.WidthLabel = wx.StaticText(self.panel, -1, label="宽度范围:", pos=(180, 100))
        self.WidthMinText = wx.TextCtrl(self.panel, -1, pos=(240, 100), size=(50, 22))
        self.SymLabel2 = wx.StaticText(self.panel, -1, label="~", pos=(300, 100))
        self.WidthMaxText = wx.TextCtrl(self.panel, -1, pos=(320, 100), size=(50, 22))
        thick_list = ['18mm', '20mm', '22mm', '25mm']
        self.ThickLabel = wx.StaticText(self.panel, -1, label="基材厚度:", pos=(180, 150))
        self.ThickCombobox = wx.ComboBox(self.panel, -1, value='18mm', pos=(250, 150), size=(100, 50),
                                            choices=thick_list)

    def get_order_amount(self):
        """
        获取需要生成的订单数
        :return: 生成的订单数
        """
        order_num_min = 1
        order_num_max = 110
        if self.OrderAmountText.GetValue().replace(' ', '') == '':  # 没有输入处理
            self.order_input_flag = False
            print u"请输入订单数！"
        else:
            if '.' in str(self.OrderAmountText.GetValue().replace(' ', '')):  # 输入小数处理
                self.order_input_flag = False
                print u"输入的订单数不合理！"
            else:
                if str(self.OrderAmountText.GetValue().replace(' ', '')).isdigit():  # 判断输入的字符串是否全为数字
                    order_num = int(self.OrderAmountText.GetValue().replace(' ', ''))  # 去除空格并转换成整数
                    if order_num >= order_num_min and order_num <= order_num_max:  # 最大最小值限制，也把输入负数，0的情况进行了处理
                        self.order_input_flag = True
                        return order_num
                    else:
                        self.order_input_flag = False
                        print u"输入的订单数不合理！"
                else:
                    print u"输入的订单数不合理！"

    def get_section_amount(self):
        """
        获取需要生成一个订单下的组件数
        :return: 生成一个订单下的组件数
        """
        section_num_min = 1
        section_num_max = 10
        if self.SectionAmountText.GetValue().replace(' ', '') == '':  # 没有输入处理
            self.section_input_flag = False
            print u"请输入组件数！"
        else:
            if '.' in str(self.SectionAmountText.GetValue().replace(' ', '')):  # 输入小数处理
                self.section_input_flag = False
                print u"输入的组件数不合理！"
            else:
                if str(self.SectionAmountText.GetValue().replace(' ', '')).isdigit():
                    section_num = int(self.SectionAmountText.GetValue().replace(' ', ''))  # 去除空格并转换成整数
                    if section_num >= section_num_min and section_num <= section_num_max:  # 最大最小值限制，也把输入负数，0的情况进行了处理
                        self.section_input_flag = True
                        return section_num
                    else:
                        self.section_input_flag = False
                        print u"输入的组件数不合理！"
                else:
                    print u"输入的组件数不合理！"

    def get_part_amount(self):
        """
        获取需要生成一个组件下的部件数
        :return:获取需要生成一个组件下的部件数
        """
        part_num_min = 1
        part_num_max = 50  # 设置部件数能够输入的最大值为50
        if self.PartAmountText.GetValue().replace(' ', '') == '':  # 没有输入处理
            self.part_input_flag = False
            print u"请输入部件数！"
        else:
            if '.' in str(self.PartAmountText.GetValue().replace(' ', '')):  # 输入小数处理
                self.part_input_flag = False
                print u"输入的部件数不合理！"
            else:
                if str(self.PartAmountText.GetValue().replace(' ', '')).isdigit():
                    part_num = int(self.PartAmountText.GetValue().replace(' ', ''))  # 去除空格并转换成整数
                    if part_num >= part_num_min and part_num <= part_num_max:  # 最大最小值限制，也把输入负数，0的情况进行了处理
                        self.part_input_flag = True
                        return part_num
                    else:
                        self.part_input_flag = False
                        print u"输入的部件数不合理！"
                else:
                    print u"输入的部件数不合理！"

    def get_data_type(self):
        """
        获取数据类型
        A类：数据特征相差不大的大型门板
        B类：数据特征相差不大的中型门板
        C类：数据特征相差不大的小型门板
        D类：数据特征相差不大的条子
        数据特征：门板长宽与面积指标
        :return:
        """
        return self.DataTypeCombobox.GetValue()

    def get_thick(self):
        """
        获取基材厚度
        :return: 基材厚度
        """
        return int(self.ThickCombobox.GetValue().split('mm')[0])

    def get_height_width_range(self):
        """
        从文本框得到高宽的最大值与最小值范围，将min H，max H, min W, max W依次存储到列表height_width_range中
        对输入框的数据合理性进行判断
        :return: 列表height_width_range
        """
        # regInt = '^\d+$'  # 只能匹配1、12、123等只包含数字的字符串
        # regFloat = '^\d+\.\d+$'  # 能匹配2.36、0.36、00069.63、0.0、263.25等
        regIntOrFloat = '^\d+$' + '|' + '^\d+\.\d+$'  # 整数或小数
        height_width_range = []
        height_min = self.HeightMinText.GetValue().replace(' ', '')  # 得到的数据类型为unicode
        height_max = self.HeightMaxText.GetValue().replace(' ', '')
        width_min = self.WidthMinText.GetValue().replace(' ', '')
        width_max = self.WidthMaxText.GetValue().replace(' ', '')
        if height_min == "" or height_max == "" or width_min == "" or width_max == "":
            self.range_input_flag = False
            print u"请正确输入生成门板高宽数据的范围！"
        else:
            # 用正则表达式判断输入的范围是否合理，即为整数或者小数
            if re.search(regIntOrFloat, height_min) and re.search(regIntOrFloat, height_max) and re.search(regIntOrFloat, width_min) and re.search(regIntOrFloat, width_max):
                height_min_float = float(height_min)
                height_max_float = float(height_max)
                width_min_float = float(width_min)
                width_max_float = float(width_max)
                if height_min_float <= height_max_float and width_min_float <= width_max_float and height_min_float >= HeightOrWidthMin and height_min_float < HeightOrWidthMax and height_max_float > HeightOrWidthMin and height_max_float <= HeightOrWidthMax and width_min_float >= HeightOrWidthMin and width_min_float < HeightAndWidthLimit and width_max_float > HeightOrWidthMin and width_max_float <= HeightAndWidthLimit:
                    self.range_input_flag = True
                    height_width_range = [height_min_float, height_max_float, width_min_float, width_max_float]
                    return height_width_range
                else:
                    self.range_input_flag = False
                    print u"输入的门板的高宽范围数据不合理，请重新输入！"
            else:
                self.range_input_flag = False
                print u"输入的门板的高宽范围数据不合理，请重新输入！"

    def create_data(self, event):
        # self.DataText.Clear()
        order_num = self.get_order_amount()
        section_num = self.get_section_amount()
        part_num = self.get_part_amount()
        # data_type = self.get_data_type()
        thick = self.get_thick()
        height_width_range = self.get_height_width_range()
        if order_num == "" or section_num == "" or part_num == "" or height_width_range == [] or thick == "":
            print u"您未输入或选择好数据"
        else:
            if self.order_input_flag and self.section_input_flag and self.part_input_flag and self.range_input_flag:
                id = ID(order_num, section_num, part_num)
                part_id = id.get_part_id()
                create_data = CreateData(order_num, section_num, part_num, height_width_range, thick)
                Door_Size = create_data.create_door_data()
                self.store_data_to_db(Door_Size, part_id, order_num, section_num, part_num, thick)
                for i in range(len(Door_Size[1])):
                    output_str1 = str("门型："+str(Door_Size[0][i])+" , "+"门板长度："+str(Door_Size[1][i])+" , "+
                                      "门板宽度："+str(Door_Size[2][i])+" , "+"门板厚度："+str(Door_Size[3][i]))
                    output_str2 = " , " + "部件号：" + part_id[i] + " , " + "所属组件号：" + part_id[i].split('P')[0]+ " , " \
                                  + "所属订单号：" + part_id[i].split('P')[0].split('S')[0] + "\r\n"
                    self.DataText.WriteText(output_str1 + output_str2)
                self.DataText.WriteText(str("\r\n" + "订单部件数：" + str(len(Door_Size[0])) + "\r\n"))

    def remove_data(self, event):
        self.OrderAmountText.Clear()
        self.SectionAmountText.Clear()
        self.PartAmountText.Clear()
        self.HeightMaxText.Clear()
        self.HeightMinText.Clear()
        self.WidthMaxText.Clear()
        self.WidthMinText.Clear()
        self.DataText.Clear()


    def cancel(self, event):
        # print "width =", GetSystemMetrics(0)  # 获取屏幕的宽度
        # print "height =", GetSystemMetrics(1)  # 获取屏幕的高度
        self.Close()
        # t = time.localtime(time.time())
        # st = time.strftime("%Y-%m-%d %H:%M:%S", t)  # 获取系统当前时间

    def store_data_to_db(self, door_info, part_id, order_num, section_num, part_num, thick):
        order_id = []
        section_id = []
        if is_connection_db():
            # 存数据到合同表单
            cursor = db.cursor()
            cursor.execute("SELECT `Index` FROM `order_contract_internal` WHERE 1  ORDER BY `Index` DESC  LIMIT 1")
            contract_id_tuple = cursor.fetchone()
            if contract_id_tuple is None:
                contract_id = 0
            else:
                contract_id = contract_id_tuple[0]
            contract_id += 1
            cursor.execute("INSERT INTO `order_contract_internal`(`Contract_id`, `Contract_C_Time`, `Order_num`, `Sec_num`, `Part_num`, `State`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (str(contract_id), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), order_num, section_num*order_num, part_num*section_num*order_num, 0))
            db.commit()
            cursor.close()
            # 存数据到部件表单
            for i in range(len(part_id)):
                section_id.append(part_id[i].split('P')[0])
                section_id = sorted(set(section_id), key=section_id.index)
                order_id.append(part_id[i].split('P')[0].split('S')[0])
                order_id = sorted(set(order_id), key=order_id.index)
                cursor = db.cursor()
                sql = "INSERT INTO `order_part_online`(`Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, `Door_thick`, `Package_state`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                      (contract_id, part_id[i].split('P')[0].split('S')[0], part_id[i].split('P')[0], part_id[i], door_info[0][i], door_info[1][i], door_info[2][i], door_info[3][i], 0)
                cursor.execute(sql)
                db.commit()
            cursor.close()
            # 存数据到零件表单
            for i in range(len(part_id)):
                section_id.append(part_id[i].split('P')[0])
                section_id = sorted(set(section_id), key=section_id.index)
                order_id.append(part_id[i].split('P')[0].split('S')[0])
                order_id = sorted(set(order_id), key=order_id.index)
                cursor = db.cursor()
                sql = "INSERT INTO `order_element_online`(`Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Board_type`, `Board_height`, `Board_width`, `Board_thick`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                      (contract_id, part_id[i].split('P')[0].split('S')[0], part_id[i].split('P')[0], part_id[i], door_info[0][i], door_info[1][i], door_info[2][i], door_info[3][i])
                cursor.execute(sql)
                db.commit()
            cursor.close()
            # 存数据到订单表单
            for i in range(order_num):
                cursor = db.cursor()
                cursor.execute("INSERT INTO `order_order_online`(`Order_id`, `Sec_num`, `Part_num`) VALUES ('%s', '%s', '%s')" %
                               (order_id[i], section_num, part_num*section_num))
                db.commit()
            cursor.close()
            # 存数据到组件表单
            for i in range(section_num*order_num):
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO `order_section_online`(`Order_id`, `Sec_id`, `Part_num`, `Package_state`) VALUES ('%s', '%s', '%s', '%s')" %
                    (section_id[i].split('S')[0], section_id[i], part_num, 0))
                db.commit()
            cursor.close()
        else:
            print u"数据库连接失败！"


class CreateData(object):
    def __init__(self, Order_amount, OneOrder_Section_amount, OneSection_Part_amount, height_width_range, thick):
        self.Order_amount = Order_amount
        self.OneOrder_Section_amount = OneOrder_Section_amount
        self.OneSection_Part_amount = OneSection_Part_amount
        self.height_width_range = height_width_range
        # self.Data_Type = Data_Type
        self.thick = thick

    def create_door_type(self):  # 随机生成MY_1701-MY_1794的94款门型
        door_type_amount = 94
        i = random.randint(1, door_type_amount)
        if i < 10:
            door_type = "MY_170" + str(i) + "_橱柜门"
        else:
            door_type = "MY_17" + str(i) + "_橱柜门"
        return door_type

    def create_door_data(self):
        """
        随机生成门板数据函数
        :return: Door_Part_Size[0]存门型，Door_Part_Size[1]存高度，Door_Part_Size[2]存宽度，Door_Part_Size[3]存厚度
        """
        Part_amount = self.OneSection_Part_amount*self.OneOrder_Section_amount*self.Order_amount  # 需要生成的总部件数
        Door_Part_Height = []
        Door_Part_Width = []
        Door_Part_Thick = []
        Door_Type = []
        Door_Type_Value = self.create_door_type()
        same_size_list = self.create_same_size_part(Part_amount)

        for i in range(same_size_list[1]):
            same_int = random.randint(0, 1)  # 加了随机生成相同尺寸的和不同尺寸的
            if same_int == 0:
                RandomHeight = round(random.uniform(self.height_width_range[0], self.height_width_range[1]))
                RandomWidth = round(random.uniform(self.height_width_range[2], self.height_width_range[3]))
            # RandomHeight = round(random.uniform(self.height_width_range[0], self.height_width_range[1]))
            # RandomWidth = round(random.uniform(self.height_width_range[2], self.height_width_range[3]))
            for j in range(same_size_list[0]):
                Door_Type.append(Door_Type_Value)
                if same_int == 1:
                    RandomHeight = round(random.uniform(self.height_width_range[0], self.height_width_range[1]))
                    RandomWidth = round(random.uniform(self.height_width_range[2], self.height_width_range[3]))
                HorW= random.randint(0, 1)  # 随机分配高宽
                if HorW == 0:
                    H = RandomHeight
                    W = RandomWidth
                else:
                    H = RandomWidth
                    W = RandomHeight
                Door_Part_Height.append(H)
                Door_Part_Width.append(W)
                Door_Part_Thick.append(self.thick)
        Door_Part_Size = [Door_Type, Door_Part_Height, Door_Part_Width, Door_Part_Thick]
        return Door_Part_Size

    def create_same_size_part(self, part_num):
        """
        随机生成尺寸相同的门板数据
        得到的prime_list为质数因子，并添加了一个1，如12=[1,2,2,3]
        :param part_num: 部件总数
        :return: part_num = same_size_num * remain_num，其中same_size_num是随机的，算法：将一个整数分解成多个质数相乘
        """
        part_num_store = part_num
        prime_list = [1]
        if not isinstance(part_num, int) or part_num <= 0:
            exit(0)
        elif part_num in [1]:
            prime_list = [1]
        while part_num not in [1]:  # 循环保证递归
            for index in xrange(2, part_num + 1):
                if part_num % index == 0:
                    part_num /= index  # let n equal to it n/index
                    if part_num == 1:  # This is the point
                        prime_list.append(index)
                    else:  # index 一定是素数
                        prime_list.append(index)
                    break
        # 优化生成相同尺寸算法，使其相同尺寸的门板块数可以达到1-12任意整数值
        same_size_num = 1
        for i in range(len(prime_list)):
            if random.randint(1, 12) > 6:
                continue
            else:
                same_size_num = same_size_num * prime_list[i]
        if same_size_num > 12:
            range_index = random.randint(1, len(prime_list))  # 随机生成1-len(prime_list)的整数，包括0与len(prime_list)
            same_size_num = prime_list[range_index - 1]
        remain_num = part_num_store / same_size_num
        return [same_size_num, remain_num]


class ID(object):
    """
    生成合同、订单、组件、部件的ID类
    协议：例如4O2S1P3表示部件号，其中O前面的4为合同id，O后面的2为订单id,S后面的1为组件id,P后面的3为部件id
    """
    def __init__(self, order_num, section_num, part_num):
        self.order_num = order_num
        self.section_num = section_num
        self.part_num = part_num

    def get_contract_id(self):
        if is_connection_db():
            cursor = db.cursor()
            cursor.execute("SELECT `Index` FROM `order_contract_internal` WHERE 1  ORDER BY `Index` DESC  LIMIT 1")
            contract_id_tuple = cursor.fetchone()
            if contract_id_tuple is None:
                contract_id = 0
            else:
                contract_id = contract_id_tuple[0]
        else:
            print u"get_contract_id(self)方法连接数据库失败！"
        contract_id += 1
        return contract_id

    def get_order_id(self):
        global order_id_num  # 存储当前的订单数
        order_id_num = self.order_num
        order_id = []
        c_id = self.get_contract_id()
        for i in range(order_id_num):
            order_id.append(str(c_id) + "O" + str(i + 1))
        return order_id

    def get_section_id(self):
        global section_id_num
        section_id_num = self.section_num
        section_id = []
        o_id = self.get_order_id()
        for i in range(len(o_id)):
            for j in range(section_id_num):
                section_id.append(o_id[i] + "S" + str(j + 1))
        return section_id

    def get_part_id(self):
        global part_id_num
        part_id_num = self.part_num
        part_id = []
        s_id = self.get_section_id()
        for i in range(len(s_id)):
            for j in range(part_id_num):
                part_id.append(s_id[i] + "P" + str(j + 1))
        return part_id


if __name__ == '__main__':
    main()