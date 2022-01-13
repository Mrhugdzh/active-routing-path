# -*- coding: utf-8 -*-
"""
@Time ： 2022/1/6 16:12
@Auth ： Mr.Hu
@File ：doMap.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
地图节点类：
    地图节点包含
        1.地图信息
        2.当前AGV信息 （如果当前此处没有AGV，那么此值为2）
        3.如果有AGV存在的话，当前的行进信息（如果没有AGV或者AGV处于最开始时，行进信息为None）
"""

import numpy as np
import pandas as pd

path = 'map.xlsx'

class MapNode(object):
    def __init__(self, num, agvNo, action=None):
        self.mapNum = num
        self.mapAgvNo = agvNo
        self.mapAction = action
        self.path = path

def getMap():
    """获取原始地图"""
    initMap = np.array(pd.read_excel(path, header=None))
    return initMap

def wantMap():
    initMap = getMap()
    print('地图的尺寸：',initMap.shape)
    map_like = np.zeros_like(initMap, dtype=MapNode)
    for i in range(initMap.shape[0]):
        for j in range(initMap.shape[1]):
            mapNum = initMap[i][j]
            agvNo = -2
            mapNode = MapNode(mapNum, agvNo)
            map_like[i][j] = mapNode

    map = map_like
    return map


if __name__ == '__main__':
    map = wantMap()
    print(map[1][1].mapNum)
