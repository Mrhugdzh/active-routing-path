# -*- coding: utf-8 -*-
"""
@Time ： 2021/12/21 14:45
@Auth ： Mr.Hu
@File ：randomPositions.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)

"""
import random
import pandas as pd
import numpy as np

Start = 0
Task = -1
Destination = 2

def getRandomStart(map):
    """获得随机起点"""
    width = map.shape[0]
    height = map.shape[1]
    x = np.random.randint(0, width)
    y = np.random.randint(0,height)

    while map[x][y].mapNum != Start:
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)

    return [x,y]


def getRandomTask(map):
    """获取随机任务"""
    width = map.shape[0]
    height = map.shape[1]
    x = np.random.randint(0, width)
    y = np.random.randint(0, height)

    while map[x][y].mapNum != Task:
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)

    return [x, y]


def getRandomDestination(map):
    """获取随机目的地"""
    width = map.shape[0]
    height = map.shape[1]
    x = np.random.randint(0, width)
    y = np.random.randint(0, height)

    while map[x][y].mapNum != Destination:
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)

    return [x, y]

if __name__ == '__main__':
    map = pd.read_excel('../map.xlsx', header=None)
    map = np.array(map)
    print('获得的随机起点为：',getRandomStart(map))
    print('获得的随机任务为：',getRandomTask(map))
    print('获得的随机终点为：',getRandomDestination(map))