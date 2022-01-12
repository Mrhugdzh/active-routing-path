# -*- coding: utf-8 -*-
"""
@Time ： 2022/1/7 9:53
@Auth ： Mr.Hu
@File ：main.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)

"""
import sys
import time
from functools import partial

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem

from agv import Ui_MainWindow
from astars import init_map, run_this, changePointToAction, initAGV, getMapList, squeeze, n, ifConflict, initAgvMapList
from utils.doMap import wantMap


class Update(QThread):
    update_date = pyqtSignal(str)

    def setList(self, agvList):
        self.agvList = agvList

    def run(self):
        # 根据前瞻步数去压缩每一个agv的行进方向，也就是说每一个agv的action中只存储9个
        squeeze(self.agvList, n)
        # 根据当前9步去加载每一步的地图信息，并且将他们同时存于agv的mapList中，不考虑冲突
        getMapList(self.agvList)
        # 根据mapList判冲突
        flag = True
        agv_list = self.agvList
        while flag:
            agv_list, flag = ifConflict(agv_list)
            print('有冲突发生', flag)
        no = 0
        minN = len(agv_list[0].result_paths[0])
        for agv in agv_list:
            minNs = len(agv.result_paths[0])
            if minN >= minNs:
                minN = minNs
        while no <= 9 and no < minN:
            for agv in agv_list:
                self.update_date.emit(
                    str(str(agv.result_paths[0][no][0]) + '  ,  ' + str(agv.result_paths[0][no][1])))
            no = no + 1
            time.sleep(0.1)


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
        self.tableWidget.setColumnCount(50)
        self.tableWidget.setRowCount(50)
        Value = "test"  # 内容
        width = self.tableWidget.width()
        height = self.tableWidget.height()
        print(width)
        print(height)

        for i in range(50):
            self.tableWidget.setColumnWidth(i, 1)  # 设置j列的宽度
            self.tableWidget.setRowHeight(i, 1)  # 设置i行的高度
        for i in range(50):
            for j in range(50):
                self.tableWidget.setItem(i, j, QTableWidgetItem(''))  # 设置j行i列的内容为Value

        # 填充颜色
        # 黑色表示货物
        # 橙色表示交付点
        # 绿色表示充电桩
        for i in range(50):
            if i % 2 != 0:
                self.tableWidget.item(i, 49).setBackground(QBrush(QColor(255, 170, 0)))
            else:
                self.tableWidget.item(i, 49).setBackground(QBrush(QColor(0, 255, 127)))
        # 设置货物
        for i in range(1, 49):
            for j in range(1, 49):
                if j % 3 != 0 and i % 5 != 0:
                    self.tableWidget.item(i, j).setBackground(QBrush(QColor(0, 0, 0)))
        self.tableWidget.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.tableWidget.horizontalHeader().setVisible(False)  # 隐藏水平表头

    def updates(self, position):
        import re
        p = re.findall(r"\d+.?\d*", position)
        y = int(p[1])
        x = int(p[0])
        self.tableWidget.item(x, y).setBackground(QBrush(QColor(255, 0, 255)))

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
