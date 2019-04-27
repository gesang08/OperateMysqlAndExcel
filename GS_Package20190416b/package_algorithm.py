#!/usr/bin/env python
# _*_ coding: UTF-8 _*_

# *****************************************************说明*************************************************************
# V20190313a:将高宽组成的全区域划分为288个区域，实现从数据库获取数据与将实际门板尺寸参数与对应的288个区域的绑定
# V20190315a:将实际板件尺寸按照区域id为key存储到字典中
# V20190318a:加error_id报错记录与处理，调增程序结构为上层函数-中层函数-底层函数管理形式，从而不显得程序杂乱
# V20190321a:完成区域超过打一包处理的函数实现
# V20190325a:将可以打一包且有剩余空间的和不可以打一包的进行统一重组处理
# V20190326a:将区域的index修改为str类型，并修改info_box_part_dicts里面的value下的index在超过一包重新编号的变动
# V20190328a:实现将不可打包移至可打包区域中，问题：1.不可打包部件很多，可打包很少，将可打包的区域填满后，就没有再处理；2.全在
#            不可打包区域没有处理
# V20190412b:初步实现打包，并输出到数据库中
# 未解决问题：1.长条子需要单独打包，短或较短的条子可以进行拼接；2.重组时，可能会将一个非常长的条子，如（30,2436）放到目标区域中
#            3.一包有最大层数限制，比如6层，但此处没有; 4.22O21S23,31O1S1,36O1S1,36O1S2四个组件未能成功打包，
#            需要考虑层数及块数限制
# **********************************************************************************************************************

import wx
import wx.lib.delayedresult as delayedresult
import MySQLdb
from collections import defaultdict
import time
import sys
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
import math

reload(sys)
sys.setdefaultencoding('utf-8')

SERVER_IP = '127.0.0.1'
USER = 'root'
PASSWORD = '12345678'
DB = 'gs_package'
PORT = 3306
CHARSET = 'utf8'

HeightOrWidthMax = 2436  # 门板高宽上限
HeightOrWidthMin = 30  # 门板高宽下限
HeightAndWidthLimit = 1200  # 门板高宽不能同时大于1200限制
OnePackageMaxWeight = 50  # 打包的重量最大值设置为50kg，最小值设置为20kg
OnePackageMinWeight = 20
BaseMaterialDensity = 765.18  # 基材密度设置为765.18kg/m^3
OneLayerMaxPlates = 10  # 一层的最大块数设置为10
OnePackageMaxLayers = 10  # 一包的最大层数设置为10


class Package():
    def __init__(self, log):
        self.start = time.clock()  # 该类调用执行开始时间
        self.log = log
        self.timer_second = wx.PyTimer(self.timer)  # wx.PyTimer继承自Timer,当计时器PyTimer到期时，将向此计时器类传递要调用的可调用对象;
        self.isrunning = False
        self.timer_second.Start(1000)  # 计时间隔interval=1000ms,打开计时器timer_second,计时器从0开始计时到1000ms，然后计时器timer_second通过wx.PyTimer(MethodName)调用MethodName方法，继续计时再计时1000ms，再次调用MethodName方法，实现每隔1秒钟调用一下MethodName方法
        self.abortEvent = delayedresult.AbortEvent()  # AbortEvent()类的实例化
        self.jobID = 0

    def timer(self):
        if self.is_new_package():
            if (self.jobID == 0):
                # self.timer_second.Stop()  # 关闭计时器timer_second
                self.jobID += 1
                delayedresult.startWorker(self._result_consumer, self._result_producer,
                                          wargs=(self.jobID, self.abortEvent), jobID=self.jobID)

    def _result_consumer(self, delayedResult):
        jobID = delayedResult.getJobID()
        assert jobID == self.jobID
        '''
        等价于代码：
        if not jobID == self.jobID:
            raise AssertionError
        '''
        self.jobID = 0
        # self.timer_second.Start(3000)

    def _result_producer(self, jobID, abortEvent):
        self.package_main()
        jobID = 0  # producer完成后把jobID = 0，producer生产的结果result为0，因为producer的返回值result为0
        return jobID

    def is_connection_db(self):
        """
        是否成功连接数据库方法
        :return: 成功为True,否则为False
        """
        try:
            self.db = MySQLdb.connect(host=SERVER_IP, user=USER, passwd=PASSWORD, db=DB, port=PORT, charset=CHARSET)
        except Exception as e:
            self.log.WriteText('打包程序is_connection_db方法报错，数据库连接不成功！ \r\n')
            print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                u"打包程序is_connection_db()方法报错，数据库连接不成功！"
            return False
        else:
            return True

    def is_new_package(self):
        """
        查询组件表单是否有需要打包的组件
        :return: 无需要打包的组件返回False,否则返回True
        """
        have_new_package = False
        if self.is_connection_db():
            cursor = self.db.cursor()
            cursor.execute("SELECT `Index`, `Sec_id` FROM `order_section_online` WHERE `Package_state`=0")
            record = cursor.fetchone()
            if record == () or record is None:
                have_new_package = False
            else:
                have_new_package = True
                self.section_id = record[1]
            self.db.close()
            return have_new_package
        else:
            return have_new_package

# *****************************************************上层方法**********************************************************
    def package_main(self):
        self.isrunning = True
        if self.is_connection_db():
            error_id, info_box_lists = self.pro_package()
            if error_id == 0:
                error_id, info_package_plies_plate = self.core_package(info_box_lists)
                if error_id == 0:
                    error_id = self.after_package(info_package_plies_plate)
                    if error_id == 0:
                        self.isrunning = False
                    else:
                        print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                              u"调用after_package()方法出现错误！"
                else:
                    print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                          u"调用core_package()方法出现错误！"
            else:
                print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                      u"调用pro_package()方法出现错误！"
        else:
            print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                  u"调用is_connection_db()方法出现错误！"
        print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
              self.section_id + u"组件打包完成！"
        end = time.clock()
        print end - self.start  # 计算程序运行时间，单位为秒

# *****************************************************中层方法**********************************************************

    def pro_package(self):
        info_box_lists = []
        error_id = self.pre_package_get_part_info()
        if error_id == 0:
            info_box_lists = self.create_virtual_box_size(self.info_parts[0][7])
        else:
            print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                  u"调用pre_package_get_part_info()方法出现错误！"
        return error_id, info_box_lists

    def core_package(self, info_box_lists):
        error_id = 0
        exist_remain = False
        error_id = self.place_part_to_range(info_box_lists)
        for value in self.remain_num_and_state.values():
            if value[1] == 0:  # 存在不可以打一包的区域
                exist_remain = True
        if error_id == 0 and exist_remain:  # 程序无异常且存在有不可打一包的才调用重组函数
            self.recombine_remain_part()

        # 部件已经放到了划分好的区域中，接下来进行每包部件下每层的具体放置情况
        info_package_plies_plate = []  # 3维列表，存放一个组件下每块部件在每包每层的信息
        package_num = 0  # 记录当前包数编号
        for key, value in self.info_box_part_dicts.items():
            if len(value) != 0:  # 剔除重组后为空的值
                plates = self.layout_2dim_simple_binary_tree(key, value)
                package_num += 1
                for plate in plates:
                    plate[-2] = 'P' + self.section_id + '-' + str(package_num)
                    # info_package_plies_plate.append(plate)
                info_package_plies_plate.append(plates)
        return error_id, info_package_plies_plate

    def after_package(self, info_package_plies_plate):
        error_id = 0
        error_id = self.send_package_info_to_work_package_task_list(info_package_plies_plate)
        if error_id == 0:
            self.update_package_info_to_db()
        else:
            print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                  u"调用after_package()方法出现错误！"
        return error_id

# *****************************************************底层方法**********************************************************

    def pre_package_get_part_info(self):
        error_id = 0
        self.info_parts = []  # 2维列表，将部件信息存储到列表中
        self.part_sizes = []  # 2维列表，存部件高宽厚与转换状态
        if self.is_connection_db():
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT `Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, `Door_thick`, `Package_state`, `Element_type_id` FROM `order_part_online` WHERE `Sec_id` = '%s'" % self.section_id)
            info_part1 = cursor.fetchall()
            if info_part1 == () or info_part1 is None:
                self.log.WriteText("打包程序pre_package_get_part_info报错，给定组件下的部件信息为空！")
                error_id = 100
            else:
                for i in range(len(info_part1)):
                    self.info_parts.append(list(info_part1[i]))
                    self.info_parts[i][8] = 0  # 不管部件表单打包状态是多少，读取部件信息的打包状态都置0
                for info_part in self.info_parts:
                    width, height, is_change_state = self.is_change_height_width(info_part[5], info_part[6])
                    part_size = [info_part[3], width, height, info_part[7], is_change_state]
                    self.part_sizes.append(part_size)
            self.db.close()
            # plt.scatter([w[1] for w in self.part_sizes], [h[2] for h in self.part_sizes])
            # plt.title('Original data')
            # plt.xlabel('width/mm')
            # plt.ylabel('height/mm')
            # plt.axis([0, 1220, 30, 2440])
            # plt.xticks(range(0, 1300, 100))
            # plt.yticks(range(0, 2500, 100))
            # plt.grid()
            # plt.show()
        return error_id

    def create_virtual_box_size(self, thick):
        """
        将30<=H<=2436,30<=W<=1200组成的2维区域细分区间，其细分算法为：100<=H<=2300，100<=W<=1200以100为间隔细分，余下30-100
        和2300-2436为一个区间，根据重量生成每个区间的最少可以放的块数和最多可以放的块数
        :return: 288 * 7二维列表info_box_lists,
        格式为[Index,short_range_low, short_range_up, long_range_low, long_range_up, box_block_low, box_block_up]
        """
        index = 0
        info_box_lists = []
        interval = 100
        long_range_num = (HeightOrWidthMax - HeightOrWidthMin) // interval  # 以100为间隔获得长度区间数为24个
        short_range_num = (HeightAndWidthLimit - HeightOrWidthMin) // interval + 1  # 以100为间隔获得宽度区间数为12个
        for i in range(short_range_num):
            for j in range(long_range_num):
                short_range_low = i * interval
                short_range_up = (i + 1) * interval
                long_range_low = j * interval
                long_range_up = (j + 1) * interval
                if j == 0:
                    long_range_low = HeightOrWidthMin
                if j == long_range_num - 1:
                    long_range_up = HeightOrWidthMax
                if i == 0:
                    short_range_low = HeightOrWidthMin
                index += 1
                box_block_low = int(round(
                    OnePackageMinWeight / (short_range_up * long_range_up * thick * 10 ** (-9) * BaseMaterialDensity)))
                box_block_up = int(round(OnePackageMaxWeight / (
                            short_range_low * long_range_low * thick * 10 ** (-9) * BaseMaterialDensity)))
                if box_block_low == 1:
                    if (np.mean([short_range_low, short_range_up]) * np.mean([long_range_low, long_range_up]) <=
                            HeightOrWidthMax * HeightAndWidthLimit / 2):  # 不超过基材一半面积的，最少可以放2块
                        box_block_low += 1
                if box_block_low == 0:
                    box_block_low += 1
                info_box_lists.append(
                    [str(index), short_range_low, short_range_up, long_range_low, long_range_up,
                     box_block_low, box_block_up])
        return info_box_lists

    def is_change_height_width(self, init_height, init_width):
        """
        :param init_height:
        :param init_width:
        :return:0表示无需转换高宽，1表示转化了高宽
        """
        if init_height >= init_width:
            return init_width, init_height, 0
        else:
            return init_height, init_width, 1

    def place_part_to_range(self, info_box_lists):
        """
        将实际的部件放到288个区间盒子里
        将实际部件放到区域里，存放在字典中的格式为self.info_box_parts={key=Index:[[part_id,width,height,thick,is_change_state,
        Index,short_range_low, short_range_up, long_range_low, long_range_up, box_block_low,box_block_up],...]}
        考虑到某个区域会出现大于一包的情况，需要对包在区域进行划分，此时将key标记为id-1,id-2,...
        self.remain_num_and_state = {key=Index:[remain_num,package_state]},remain_num存储包的剩余可放块数，package_state
        记录包的状态:-1表示初始化，0表示不可打一包，1表示可打一包，2表示正好一包,5表示不可打一包且包里块数为0
        """
        error_id = 0
        part_info_and_ranges = []
        range_nums = []
        self.info_box_part_dicts = defaultdict(list)  # info_box_part_dicts以区域id为键，以实际板件信息为值的字典,存放实际部件所放得区域
        self.remain_num_and_state = defaultdict()
        is_finish_put_in_range = False
        for part_size in self.part_sizes:
            for box_size in info_box_lists:  # ( ]范围是包含右边不包含左边，所以当部件高宽为30时，此部件信息会丢失，所以需要考虑部件高宽为30的情况
                if ((part_size[1] > box_size[1]) and (part_size[1] <= box_size[2]) and (part_size[2] > box_size[3])
                    and (part_size[2] <= box_size[4])) or ((part_size[1] >= HeightOrWidthMin) and
                                                           (part_size[1] <= box_size[2]) and
                                                           (part_size[2] >= HeightOrWidthMin) and
                                                           (part_size[2] <= box_size[4])):
                    part_info_and_ranges.append(part_size + box_size)
                    break
                else:
                    continue
        part_info_and_ranges.sort(key=lambda x: x[5])  # 按288个区域的Index进行排序
        for row in part_info_and_ranges:
            range_nums.append(row[5])
        # key = list(set(range_nums))  # 整合列表中的重复元素，使列表元素不重复，并将其按照大小进行排序
        # key.sort(key=range_nums.index)
        for i in range(len(part_info_and_ranges)):
            for range_num in range_nums:
                if range_num == part_info_and_ranges[i][5]:
                    self.info_box_part_dicts[range_num].append(part_info_and_ranges[i])
                    break
                else:
                    continue
        for key, value in self.info_box_part_dicts.items():
            self.remain_num_and_state[key] = [value[0][11], -1]
        # temp_box_part_dicts = self.info_box_part_dicts
        for key, value in self.info_box_part_dicts.items():  # 优先级大小：超过一包>可以打一包>不可以打一包
            if len(value) > value[0][11]:
                # self.is_recombine_package = 1
                del self.info_box_part_dicts[key]
                del self.remain_num_and_state[key]
                # print u"超过一包"
                # print key, value
                error_id = self.beyond_one_package_handle(key, value)
            else:
                if (len(value) >= value[0][10]) and (len(value) <= value[0][11]):
                    # self.is_recombine_package = 0
                    if len(value) == value[0][11]:
                        self.remain_num_and_state[key] = [value[0][11] - len(value), 2]
                    else:
                        self.remain_num_and_state[key] = [value[0][11] - len(value), 1]
                    # print u"可以打一包"
                    # print key, value
                else:
                    if len(value) < value[0][10]:
                        # self.is_recombine_package = -1
                        self.remain_num_and_state[key] = [value[0][11] - len(value), 0]
                        # print u"不能够打一包，从临近且有部件的区域寻找，进行重组"
                        # print key, value
                        # self.less_one_package_handle(key, value)
                    else:
                        error_id = 110
        return error_id

    def beyond_one_package_handle(self, key, value):
        """
        按H为第一优先级，W为第二优先级进行升级排序，截取以box_block_up个数进行划分，此处缺点是截取点左右可能有相同尺寸的部件，
        导致相同尺寸可能不能放在一起进行打包
        :param key:
        :param value:二维列表
        :return:
        """
        error_id = 0
        value.sort(key=lambda x: (x[2], x[1]))  # 将其按H为第一优先级，W为第二优先级进行排序
        if len(value) % value[0][-1] == 0:
            id_i = len(value) / value[0][-1]
        else:
            id_i = len(value) / value[0][-1] + 1
        j = 1  # 累计划分的包数
        package_i = 1  # 累计划分的块数到box_block_up
        for i in range(len(value)):
            if j < id_i:
                if package_i < value[0][-1]:
                    value[i][5] = key + "-" + str(j)
                    self.info_box_part_dicts[key + "-" + str(j)].append(value[i])
                    package_i += 1
                else:
                    value[i][5] = key + "-" + str(j)
                    self.info_box_part_dicts[key + "-" + str(j)].append(value[i])
                    self.remain_num_and_state[key + "-" + str(j)] = [0, 2]
                    package_i = 1
                    j += 1
            elif j == id_i:
                value[i][5] = key + "-" + str(j)
                self.info_box_part_dicts[key + "-" + str(j)].append(value[i])
                remain_num = len(value) - (id_i - 1) * value[0][-1]
                if remain_num == value[0][-1]:
                    self.remain_num_and_state[key + "-" + str(j)] = [value[0][-1] - remain_num, 2]
                if (remain_num >= value[0][-2]) and (remain_num < value[0][-1]):
                    self.remain_num_and_state[key + "-" + str(j)] = [value[0][-1] - remain_num, 1]
                if remain_num < value[0][-2]:
                    # print u"不能打一包，须重组！"
                    self.remain_num_and_state[key + "-" + str(j)] = [value[0][-1] - remain_num, 0]
            else:
                error_id = 105
        return error_id

    def recombine_remain_part(self):
        """
        将不能够打一包的区域进行重组recombine
        算法：先将区域剩余块数比较少的优先按照部件尺寸距离区域中心最近的板子放到该区域，计算当前包数的重量，如果当前区域大于该
        区域重量最大容量，停止往该区域放板子
        :return:
        """
        remain_lists = []
        remain_lists1 = []
        remain_lists2 = []
        remain_lists3 = []
        weight = 0
        current_weight = 0
        for key, value in self.remain_num_and_state.items():
            for row in self.info_box_part_dicts[key]:
                weight = weight + row[1] * row[2] * row[3] * BaseMaterialDensity / (10 ** 9)
            remain_lists.append([key, value[0], value[1], self.info_box_part_dicts[key][0][-1], round(weight, 4)])
            weight = 0
        remain_lists.sort(key=lambda x: (x[4], x[2]), reverse=False)  # 按照区域所放得部件重量和包状态进行升序排序
        # 若有可打一包的，取包重量最小为为目标区域；若无可打一包的，取不可打一包的重量最大为为目标区域
        for remain_list in remain_lists:
            if remain_list[2] == 0:
                remain_lists1.append(remain_list)  # 不可打一包的放remain_lists1中
            elif remain_list[2] == 1:
                remain_lists2.append(remain_list)  # 可打一包的放remain_lists2中
            else:
                remain_lists3.append(remain_list)  # 正好打一包的放remain_lists3中
        remain_lists1.sort(key=lambda x: x[4], reverse=True)
        remain_lists = remain_lists2 + remain_lists1
        is_finish = False
        for i in range(len(remain_lists)):
            if is_finish or ((not 1 in [recombine[2] for recombine in remain_lists]) and len(remain_lists) == 1):  # 组件下有且仅有一包且不能够打一包,此时把这些部件放在一包
                break
            if self.info_box_part_dicts[remain_lists[i][0]] != []:
                target_key = remain_lists[i][0]
            else:
                continue
            current_weight = remain_lists[i][4]
            while current_weight < OnePackageMaxWeight:
                is_recombine_area, part_id, weight = self.find_one_most_suitable_part(target_key, self.info_box_part_dicts[target_key][0][6:10])
                current_weight = current_weight + weight
                if (0 not in [r[1] for r in self.remain_num_and_state.values()]) or (not is_recombine_area):
                    is_finish = True
                    break
        # print remain_lists

    def find_one_most_suitable_part(self, target_key, range_lists):
        """
        寻找当前没有放好的部件，使其离目标区域中心距离最近，注：要考虑尺寸相同时不止一块的情况
        :param range_lists:
        :return:
        """
        is_recombie_area = True
        part_id = ''
        weight = 0
        x_center = (range_lists[0] + range_lists[1]) / 2.0
        y_center = (range_lists[2] + range_lists[3]) / 2.0
        remain_list_3Ds = []
        remain_list_2Ds = []
        for k, v in self.remain_num_and_state.items():
            if k != target_key:  # 将不是当前区域k的部件放到目标区域key
                if v[0] != 0:  # 当前区域k有可剩余空间放
                    if v[1] == 0:  # 从不可打一包的里面找
                        remain_list_3Ds.append(self.info_box_part_dicts[k])
        for row in remain_list_3Ds:
            for r in row:
                remain_list_2Ds.append(r)
        if len(remain_list_2Ds) == 0:
            is_recombie_area = False
            part_id = ''
            weight = 0
        # 将所有没有放好部件按照到目标区域的距离进行升序排序，取第一个部件即离目标区域中心距离最近的部件,尺寸相同也考虑在内
        if is_recombie_area:
            remain_list_2Ds.sort(key=lambda x: (x[1] - x_center) ** 2 + (x[2] - y_center) ** 2)
            part_id = remain_list_2Ds[0][0]
            weight = round(remain_list_2Ds[0][1] * remain_list_2Ds[0][2] * remain_list_2Ds[0][3] * BaseMaterialDensity / (10 ** 9), 4)
            current_key = remain_list_2Ds[0][5]
            for row in self.info_box_part_dicts[current_key]:
                if part_id in row:
                    self.info_box_part_dicts[current_key].remove(row)
                    self.info_box_part_dicts[target_key].append(row)
            if self.info_box_part_dicts[current_key] == []:
                self.remain_num_and_state[current_key][1] = 5
            self.remain_num_and_state[current_key][0] = self.remain_num_and_state[current_key][0] + 1
            self.remain_num_and_state[target_key][0] = self.remain_num_and_state[target_key][0] - 1
            target_box_block_up = self.info_box_part_dicts[target_key][0][-1]
            if self.remain_num_and_state[target_key][0] == target_box_block_up:
                self.remain_num_and_state[target_key][1] = 2
            else:
                self.remain_num_and_state[target_key][1] = 1
        return is_recombie_area, part_id, weight

    def layout_2dim(self, key, value):
        """
        本方法实现打包2维层排样
        :param key:
        :param value:
        :return:plates列表，记录该层每块部件所放置的信息
        plates协议：
        2维列表，列数12
        [part_id,width,height,thick,is_change_state,Index,x,y,low_x_remain,low_y_remain,is_change,plies_id]
        low_x_remain、low_y_remain：当前部件放好之后，剩余的x、y方向空间
        """
        plates = [[0 for col in range(12)] for row in range(len(value))]
        value.sort(key=lambda x: (x[2], x[1]), reverse=True)
        max_part_height = value[0][2] + 20  # 取这个区域中部件高度最大的为x轴长度,20表示左右有10mm的摆动量
        max_part_width = max(x[1] for x in value) + 20  # 取这个区域中部件宽度最大的为y轴长度
        current_row = 0  # 当前最低水平线，其值表示该水平线与x轴的距离
        spill = False  # 设置每一层能放得最大块数为10，超过10块，则会溢出
        for i in range(len(plates)):  # 遍历这包部件，找到一个合适的放到plates中
            if i == 0:  # 首先放好第一块到plates,把该块从value中删除
                is_change = 0
                layer = 1  # 层数
                current_row = 1
                plates[0] = value[0][0:6] + [0, 0, max_part_height - value[0][2], max_part_width, is_change, layer]
                del value[0]
            else:
                if len(value) != 0:
                    for j in range(len(value)):
                        if value[j][2] <= plates[i][8] and value[j][1] <= plates[i][9]:  # 剩余空间可以将部件横着放入其中
                            is_change = 0
                            plates[i][0:6] = value[j][0:6]
                        elif value[j][1] <= plates[i][8] and value[j][2] <= plates[i][9]:
                            is_change = 1
                            plates[i][0:6] = value[j][0:6]

    def layout_2dim_simple_binary_tree(self, key, value):
        """
        简单二叉树方法排每一层
        :param key:
        :param value:
        :param height:
        :param width:
        :return:
        """
        value.sort(key=lambda x: (x[2], x[1]), reverse=True)
        value = [row + [0] for row in value]  # 增加一列记录状态
        height_list = [row[2] for row in value]
        width_list = [row[1] for row in value]
        if len(value) <= OnePackageMaxLayers:  # 这样控制最大层数不好
            max_part_height = max(height_list) + 20  # 取当前包的最大height并加上20可移动量为区域高度
            max_part_width = max(width_list) + 20  # 取当前包的最大width并加上20可移动量为区域宽度
        else:
            max_part_height = round(np.mean(height_list) + max(height_list))
            max_part_width = round(np.mean(width_list) + max(width_list))
        layer_num = 0
        plates = []
        """
        plates列表：
        column 12列字段协议:
        [x,y,low_x_length,low_y_length,is_change,height,width,is_change_state,thick,plies_num,package_num,part_id]
        x,y:以右上角为坐标原点，向右为x+，向下为y+建立坐标系
        low_x_length,low_y_length：最低水平线(以距离x轴距离为依据)的坐标x轴长度与y轴长度
        is_change：low_x_length,low_y_length是否转变，0为不转变，1为转变
        plies_num,package_num：该部件属于第几层；该部件属于第几包
        is_change_state:部件高宽是否旋转，0不旋转，1旋转
        """
        left_area = max_part_height * max_part_width
        while len(value) != 0:
            current_level = 0  # 当前水平线
            total_level = 1
            position = 0
            spill = False
            Plate = [[0 for col in range(12)] for row in range(len(value) * 10)]
            Plate[0] = [0, 0, max_part_height, max_part_width, 0, 0, 0, 0, 0, 0, 0, 0]
            while (current_level < total_level):  # 加入这个条件主要是为了，判断每一块新生成的板能否容下未排样的部件
                long_edge = Plate[current_level][2]
                short_edge = Plate[current_level][3]
                for i in range(0, len(value)):
                    if value[i][-1] == 0:  # 0表示部件没放好
                        if ((long_edge >= value[i][2]) and (short_edge >= value[i][1])):  # 芯板能放进去
                            if position >= OneLayerMaxPlates:  # 每层最多放10块,多于10块，溢出
                                spill = True
                                break
                            value[i][-1] = 1  # 1表示部件可放
                            position += 1
                            left_area = left_area - value[i][2] * value[i][1]
                            Plate[current_level][5] = value[i][2]
                            Plate[current_level][6] = value[i][1]
                            Plate[current_level][7] = value[i][4]
                            Plate[current_level][8] = value[i][3]
                            Plate[current_level][11] = value[i][0]  # 把该部件的编号放入Plate列表里，用于输出生成工位工单
                            if ((value[i][2] >= short_edge - value[i][1]) and (
                                    Plate[current_level][4] == 0)):  # 新生成第一块待填充芯板是横的，且上一块待填充芯板是横的
                                Plate[total_level][4] = 0  # 当前待填充芯板的旋转状态为0
                                Plate[total_level][2] = value[i][2]  # 待填充芯板的尺寸
                                Plate[total_level][3] = short_edge - value[i][1]
                                Plate[total_level][0] = Plate[current_level][0]  # 赋值左下角坐标
                                Plate[total_level][1] = Plate[current_level][1] + value[i][1]
                            elif ((value[i][2] < short_edge - value[i][1]) and (
                                    Plate[current_level][4] == 0)):  # 新生成第一块待填充芯板是竖直的，且上一块待填充芯板是横的
                                Plate[total_level][4] = 1
                                Plate[total_level][2] = short_edge - value[i][1]  # 赋值当前待填充芯板的尺寸
                                Plate[total_level][3] = value[i][2]
                                Plate[total_level][0] = Plate[current_level][0]
                                Plate[total_level][1] = Plate[current_level][1] + value[i][1]
                            elif ((value[i][1] >= long_edge - value[i][2]) and (Plate[current_level][4] == 1)):
                                Plate[total_level][2] = value[i][1]
                                Plate[total_level][3] = long_edge - value[i][2]
                                Plate[total_level][4] = 0
                                Plate[total_level][0] = Plate[current_level][0]
                                Plate[total_level][1] = Plate[current_level][1] + value[i][2]
                            elif ((value[i][1] < long_edge - value[i][2]) and (
                                    Plate[current_level][4] == 1)):  # 新生成的第一块待填充芯板是竖直的，并且上一块待填充芯板是竖直的
                                Plate[total_level][3] = value[i][1]
                                Plate[total_level][2] = long_edge - value[i][2]
                                Plate[total_level][4] = 1
                                Plate[total_level][0] = Plate[current_level][0]
                                Plate[total_level][1] = Plate[current_level][1] + value[i][2]

                            if ((short_edge <= long_edge - value[i][2]) and (
                                    Plate[current_level][4] == 0)):  # 新生成的第二块可填充区域是横的，且上一块待填充区域也是横的（四种情况）
                                Plate[total_level + 1][4] = 0  # 旋转状态
                                Plate[total_level + 1][3] = short_edge  # 赋值可填充区域长度
                                Plate[total_level + 1][2] = long_edge - value[i][2]
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][2]  # 赋值左下角坐标
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            elif ((short_edge > long_edge - value[i][2]) and (Plate[current_level][4] == 0)):
                                Plate[total_level + 1][4] = 1
                                Plate[total_level + 1][3] = long_edge - value[i][2]
                                Plate[total_level + 1][2] = short_edge
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][2]
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            elif ((long_edge >= short_edge - value[i][1]) and (Plate[current_level][4] == 1)):
                                Plate[total_level + 1][4] = 1
                                Plate[total_level + 1][3] = short_edge - value[i][1]
                                Plate[total_level + 1][2] = long_edge
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][1]
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            elif ((long_edge < short_edge - value[i][1]) and (Plate[current_level][4] == 1)):
                                Plate[total_level + 1][4] = 0
                                Plate[total_level + 1][2] = short_edge - value[i][1]
                                Plate[total_level + 1][3] = long_edge
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][1]
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            total_level = total_level + 2
                            del value[i]
                            break
                if spill:
                    break
                current_level += 1
            layer_num += 1  # 记录部件所属当前层数
            if layer_num > 11:
                print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                      u"该包超过10层，请重新打！"
                break
            for plate in Plate:
                if plate[-1] != 0:
                    plate[-3] = layer_num
                    plates.append(plate)
        return plates

    def send_package_info_to_work_package_task_list(self, info_package_plies_plate):
        """
        将包信息存储到work_package_task_list表单
        存到每层部件信息字段Plies1_element_information1的协议：
        x & y & height & width & is_change & part_id
        is_change：low_x_length,low_y_length是否转变，0为不转变，1为转变
        :param info_package_plies_plate:
        :return:
        """
        error_id = 0
        split_sym = '&'
        if self.is_connection_db():
            for package in info_package_plies_plate:  # 对组件下每一包进行循环，一包对应work_package_task_list表单一条记录
                package_id = package[-1][-2]
                total_plies = max([row[-3] for row in package])
                total_area = sum([row[5] * row[6] / (10 ** 6) for row in package])
                sec_id = package[-1][-1].split('P')[0]
                create_package_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                ij = [row[-3] for row in package]
                same_count = Counter(ij)
                cursor = self.db.cursor()
                cursor.execute("INSERT INTO `work_package_task_list`(`Ap_id`, `Total_plies`, `Total_area_gs`, `Sec_id`, `Create_Time`, `Long`, `Short`, `Order_id`, `Package_num`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (package_id, total_plies, total_area, sec_id, create_package_time, package[0][2], package[0][3], sec_id.split('S')[0], len(package)))
                self.db.commit()
                cursor.close()
                for i in range(total_plies):  # 循环层数
                    element_info = [row for row in package if row[-3] == i + 1]
                    num_plies_i = 'Num_plies' + str(i + 1)
                    for j in range(same_count[i + 1]):  # 循环层下面的块数
                        current_part_id = element_info[j][-1]
                        plies_i_element_information_j = 'Plies' + str(i + 1) + '_element_information' + str(j + 1)
                        seq = (str(element_info[j][0]), str(element_info[j][1]), str(element_info[j][5]), str(element_info[j][6]), str(element_info[j][4]), str(element_info[j][-1]))
                        element_str = split_sym.join(seq)
                        cursor = self.db.cursor()
                        cursor.execute("UPDATE `work_package_task_list` SET `%s`='%s', `%s`='%s' WHERE  `Ap_id`='%s'" % (plies_i_element_information_j, element_str, num_plies_i, same_count[i + 1], str(package_id)))
                        self.db.commit()
                        cursor = self.db.cursor()  # 更新order_part_online表单部件所属的package_id
                        cursor.execute("UPDATE `order_part_online` SET `Package_task_list_ap_id` = '%s' WHERE `Part_id` = '%s'" % (package_id, current_part_id))
                        self.db.commit()
            self.db.close()
        else:
            error_id = 105
            print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                  u"调用send_package_info_to_work_package_task_list()方法出现错误！"
        return error_id

    def update_package_info_to_db(self):
        error_id = 0
        if self.is_connection_db():
            cursor = self.db.cursor()
            cursor.execute("UPDATE `order_section_online` SET `Package_state` = 5 WHERE `Sec_id` = '%s'" % (self.section_id))
            self.db.commit()
            self.db.close()
        else:
            error_id = 105
            print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                  u"调用update_package_info_to_db()方法出现错误！"
        return error_id
