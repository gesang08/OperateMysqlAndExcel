#!/usr/bin/env python
# _*_ coding: UTF-8 _*_

"""
理解以下概念和访问：
1.类的实例化方法（简称实例方法）：类本身和类实例都可以访问类实例方法
2.类的实例化属性(或类的实例化变量)：类本身和类实例都可以访问类实例属性(变量)
3.类本身直接访问方法：类本身可以直接访问类实例方法和类方法
4.类属性(类变量):
5.静态方法(@staticmethod修饰)：类本身和类实例都可以访问静态方法
6.类方法(@classmethod修改)：类本身和类实例都可以访问类方法
7.属性方法(@property)
"""


class Test:
    cls_var = '我是类变量'   # 类变量：1.不能在类实例方法下访问，可通过加self.转成实例变量访问;2.不能在类方法下访问，可通过加cls.转成cls.变量访问;

    def __init__(self, id, name, age):
        self.id = id
        self.name = name
        self.age = age

    def print_name(self, sex):  # 实例方法，而不是类方法：第一个参数为self，看到有self表示的就是实例方法，self代指的是实例，相当于C#中的this
        print self.name
        print sex

    @classmethod    # 类方法：使用@classmethod装饰器定义，第一个参数为cls.
    def print_school(cls, school):  # 注意类方法中:1.不能访问本类下的类实例属性(变量)，例如在该类方法中，不能通过self.id访问类实例属性，用cls.id访问也是不行的
                                                #  2.不能访问本类下的类实例方法，例如在该类方法中，不能通过self.print_name('boy')访问类方法，用cls.print_name('boy')访问也是不行的
        print school
        cls.school = school  # 加cls.后，可供类实例和类本身访问

    @staticmethod   # 静态方法：使用@staticmethod装饰器定义，参数列表无需加self或cls
    def print_age(your_name):   # 注意静态方法中:1.不能访问本类下的类实例属性(变量)，例如在该类方法中，不能通过self.id访问类实例属性，用cls.id访问也是不行的
                                            #   2.不能访问本类下的类实例方法，例如在该类方法中，不能通过self.print_name('boy')访问类方法，用cls.print_name('boy')访问也是不行的
        print your_name

    @property   # 属性方法：将类实例方法装饰成类实例属性，即方法转成属性(变量)
    def run(self):  # 注意：1.定义时，在实例方法的基础上添加 @property 装饰器；2.仅有一个self参数；
                        # 3.访问时，无需括号，且最好有接收的内存变量(否则有警告)，如t=test.run;4.最好有return值，否则有警告。
        ret = "该溜了"
        print ret
        return ret


if __name__ == '__main__':
    test = Test(10, 'ge sang', 24)  # 类的实例化（可称为实体）

    test.print_name('boy')   # 类实例访问类实例方法
    Test(11, 'gs', 23).print_name('boy')  # 类本身访问类实例方法

    test.print_school('天津大学')   # 类实例访问类方法
    Test(12, 'g', 22).print_school('南开大学')  # 类本身访问类方法

    print test.age  # 类实例访问类实例属性(变量)
    print Test(13, '桑', 21).age  # 类本身访问类实例属性(变量)

    print test.school   # 类实例访问cls.变量
    print Test(14, '宏', 20).school  # 类本身访问cls.变量

    test.print_age('黄')  # 类实例访问静态方法
    Test(14, '黄', 20).print_age('黄陈')  # 类本身访问静态方法

    print test.cls_var  # 类实例访问属性(变量)
    print Test(14, '黄', 20).cls_var  # 类本身访问类属性(变量)

    t = test.run
    t1 = Test(14, '黄', 20).run

    print type(Test)    # output:<type 'classobj'>，表示类对象（python中类对象可以理解为类本身，它与类的实例化是不一样的，这点和C#有很大区别）
    print type(test)    # output:<type 'instance'>，表示类的实例化
    print id(Test)  # 40146984，类对象（类本身）在内存中的引用（地址）
    print id(test)  # 47831816，类的实例化在在内存中的引用，它与类对象在内存中的引用不同，即处于不同的内存空间
