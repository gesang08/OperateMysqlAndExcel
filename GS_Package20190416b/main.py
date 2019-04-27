#!/usr/bin/env python
# _*_ coding: UTF-8 _*_

# *****************************************************说明*************************************************************
# V20190301a:正确将打包排样的YLP程序从主程序抽离移植出来，并且运行程序后，可进行打包排样
# **********************************************************************************************************************

import wx
import wx.lib.mixins.inspection
import numpy
import time
import ID_DEFINE
import math
from MyLogCtrl import MyTextCtrl
from MyLogCtrl import MyLog
# from package_gs import *
# from package_algorithm import *  #避免通配符*的使用
import package_algorithm

import sys
reload(sys)
sys.setdefaultencoding('utf8')


def main():
    app = MyApp()
    app.MainLoop()

class MyApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    def OnInit(self):
        mainframe = MyFrame(parent=None, id=wx.ID_ANY, title="YLP打包程序移植", pos=wx.DefaultPosition, size=(1200,800),
                                style=wx.DEFAULT_FRAME_STYLE)
        mainframe.Center(dir=wx.BOTH)
        # mainframe.Show()
        self.SetTopWindow(mainframe)
        return True

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self.panel = wx.Panel(self, -1, size=(1200, 800))
        self.log = self.CreateTextCtrl()
        self.package = package_algorithm.Package(self.log)
        # self.package = Package(self.log)

    def CreateTextCtrl(self, ctrl_text=""):
        t = time.localtime(time.time())
        st = time.strftime("%Y年%m月%d日 %H:%M:%S   ", t)
        if ctrl_text.strip():
            text = ctrl_text
        else:
            text = ""
        return MyTextCtrl(self.panel, -1, text, wx.Point(0, 500), wx.Size(1200, 200),
                           wx.NO_BORDER | wx.TE_MULTILINE)


if __name__ == '__main__':
    main()