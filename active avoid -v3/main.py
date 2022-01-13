# -*- coding: utf-8 -*-
"""
@Time ： 2022/1/7 9:53
@Auth ： Mr.Hu
@File ：main.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)

"""
import copy
import sys
import time
from functools import partial

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem

from agv import Ui_MainWindow
from astars import init_map, run_this, changePointToAction, initAGV, getMapList, squeeze, n, ifConflict, initAgvMapList, \
    getPosition, getAgv, goAction
from utils.doMap import wantMap


class Update(QThread):
    update_date = pyqtSignal(str)

    def setList(self, agvList):
        self.agvList = agvList

    def run(self):
        n = 9 # 前瞻步数
        num = 0
        while 1:
            flags = True
            # 根据前瞻步数去压缩每一个agv的行进方向，也就是说每一个agv的action中只存储9个
            squeeze(self.agvList, n)
            # 根据当前9步去加载每一步的地图信息，并且将他们同时存于agv的mapList中，不考虑冲突
            getMapList(self.agvList)
            # 根据mapList判冲突
            flag = True
            agv_list = copy.deepcopy(self.agvList)
            while flag:
                agv_list, flag = ifConflict(agv_list)

            print('\n此次AGV之间行进已经没有冲突，开始行进')
            print('=' * 20)
            try:
                # 去各个map中agv的位置，然后进行传输
                for nowMap in agv_list[0].mapList:
                    for agv in agv_list:
                        position = getPosition(nowMap, agv)
                        # 只传输第一次的位置
                        self.update_date.emit(
                            str(str(agv.no) + '  ,  ' + str(position[0]) + '  ,  ' + str(position[1])) + '   ,   ' + str(
                                agv.prePosition[0]) + '  ,  ' + str(agv.prePosition[1]))
                        agv.prePosition = position
                        time.sleep(0.1)
            except:
                print('发生错误')

            print('=' * 20)

            # 行进完之后修改地图信息
            map = agv_list[0].mapList[-1]
            for i in range(map.shape[0]):
                for j in range(map.shape[1]):
                    if map[i][j].mapAgvNo == agv.no:
                        agv.now_position = [i, j]
            for agv in agv_list:
                agv.mapList.clear()
                agv.mapList.append(map)
                # 修改action_path信息
                agv.action_path = copy.deepcopy(agv.agvNowAction)
                # 删除action_path的前九个动作
                if agv.nowTask:
                    if len(agv.result_paths) > 0:
                        print(agv.action_path)
                        agv.action_path.pop(0)
                        agv.result_paths.pop(0)
                        print('完成任务之后的agv path{}'.format(agv.result_paths))
                        print(agv.action_path)
                        agv.nowTask = False
                else:
                    if len(agv.action_path[0]) >= n - 1:
                        del agv.action_path[0][:n - 1]
                        print('删除之后 的action——path', agv.action_path[0])
                        print(len(agv.action_path[0]))
                        if len(agv.action_path[0]) == 1:
                            # 走最后一步
                            action = agv.action_path[0][0]
                            baseAction = goAction(action)
                            nowPositioin = agv.now_position
                            newPosition = []
                            newPosition = [nowPositioin[0] + baseAction[0], nowPositioin[1] + baseAction[1]]
                            agv.prePosition = newPosition
                            # self.update_date.emit(
                            #     str(str(agv.no) + '  ,  ' + str(position[0]) + '  ,  ' + str(
                            #         position[1])) + '   ,   ' + str(
                            #         agv.prePosition[0]) + '  ,  ' + str(agv.prePosition[1]))
                            agv.now_position = newPosition
                            agv.action_path.pop(0)
                            agv.result_paths.pop(0)
                            print('删除之后是空的')
                            print('完成任务之后的agv path{}'.format(agv.result_paths))

                        elif len(agv.action_path[0]) == 0:
                            agv.action_path.pop(0)
                            agv.result_paths.pop(0)
                            print('删除之后是空的')
                            print('完成任务之后的agv path{}'.format(agv.result_paths))
                        print(agv.action_path)

                if len(agv.action_path) == 0:
                    print('agv{}的任务已经全部完成'.format(agv.no))
                    agv.agvAllDo = True
                    print('agv{}的Alldone为{}'.format(agv.no, agv.agvAllDo))
                flags = flags and agv.agvAllDo

                # 修改AGV的初始位置
                agv.initPosition = agv.now_position
                print('修改AGV的初始位置为：', agv.initPosition)
            self.agvList = copy.deepcopy(agv_list)

            if flags:
                print('任务全部完成')
                break


class Main(QMainWindow, Ui_MainWindow, QObject):

    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)
        self.table()
        self.pushButton.clicked.connect(self.getNum)
        self.pushButton_2.clicked.connect(self.runThis)

    def runThis(self):
        self.agvList = initAgvMapList(self.agvList, self.map)
        for agv in self.agvList:
            for n in range(len(agv.tasks)):
                x = agv.tasks[n][0]
                y = agv.tasks[n][1]
                self.tableWidget.item(x, y).setBackground(QBrush(QColor(0, 0, 255)))
                self.tableWidget.item(x, y).setText('agv' + str(agv.no) + '\'s task' + str(n))
        map = init_map(self.agvList)
        run_this(map, self.agvList)
        self.map = map
        # 根据节点信息为AGV方向信息
        changePointToAction(self.agvList)
        print('路径规划完毕')

    def getNum(self):
        agvNum = self.lineEdit.text()
        taskNum = self.lineEdit_2.text()
        agvNum = int(agvNum)
        taskNum = int(taskNum)
        self.map = wantMap()
        self.agvList, _ = initAGV(agvNum, self.map, taskNum)
        self.showinfo()

    def showinfo(self):
        self.table()

        """展示基础信息，并在图中标出AGV所在的位置"""
        for agv in self.agvList:
            x = agv.start[0]
            y = agv.start[1]
            self.tableWidget.item(x, y).setBackground(QBrush(QColor(0, 255, 0)))

    def table(self):
        # 初始表格的问题 地图的尺寸： (51, 50)
        self.tableWidget.setColumnCount(51)
        self.tableWidget.setRowCount(51)
        Value = "test"  # 内容
        width = self.tableWidget.width()
        height = self.tableWidget.height()
        print(width)
        print(height)

        for i in range(51):
            self.tableWidget.setColumnWidth(i, 1)  # 设置j列的宽度
            self.tableWidget.setRowHeight(i, 1)  # 设置i行的高度
        for i in range(51):
            for j in range(51):
                self.tableWidget.setItem(i, j, QTableWidgetItem(''))  # 设置j行i列的内容为Value

        # 填充颜色
        # 黑色表示货物
        # 橙色表示交付点
        # 绿色表示充电桩
        for i in range(50):
            if i % 2 != 0:
                self.tableWidget.item(i, 50).setBackground(QBrush(QColor(255, 170, 0)))
            else:
                self.tableWidget.item(i, 50).setBackground(QBrush(QColor(0, 255, 127)))
        # 设置货物
        for i in range(1, 50):
            for j in range(1, 49):
                if j % 3 != 0 and i % 5 != 0:
                    self.tableWidget.item(i, j).setBackground(QBrush(QColor(0, 0, 0)))
        self.tableWidget.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.tableWidget.horizontalHeader().setVisible(False)  # 隐藏水平表头


    def updates(self, position):
        try:
            import re
            p = re.findall(r"\d+.?\d*", position)
            agvNo = int(p[0])
            y = int(p[2])
            x = int(p[1])
            x_old = int(p[3])
            y_old = int(p[4])
            agv = getAgv(agvNo, self.agvList)
            r = agv.color[0]
            g = agv.color[1]
            b = agv.color[2]
            self.tableWidget.item(x_old, y_old).setBackground(QBrush(QColor(255, 255, 255)))
            self.tableWidget.item(x, y).setBackground(QBrush(QColor(r, g, b)))
        except:
            print('发生错误')

    def getList(self):
        return self.agvList


def gogogo(update):
    update.start()


def goThis(update, main):
    update.setList(main.agvList)
    update.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    update = Update()
    update.update_date.connect(main.updates)
    main.pushButton_3.clicked.connect(partial(goThis, update, main))
    main.show()
    # 显示界面

    sys.exit(app.exec_())
