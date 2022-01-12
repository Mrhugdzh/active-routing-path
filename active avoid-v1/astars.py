# -*- coding: utf-8 -*-
"""
@Time ： 2021/12/21 9:36
@Auth ： Mr.Hu
@File ：astars.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
解决冲突的规则：
    1.通过等待，使得冲突AGV驶离————增加时间
        等待的步骤在三步之内，可以等待
    2.增加转向，不增加距离代价————增加时间
        当前地点有障碍，所以按照增加转向的方式，进行选择，转向修正变为减去k值，从而加强转向的机会
    3.增加路径长度，选择其他路径————增加时间，增加路径
        反其道而行，绕行过去冲突的区域
"""
import copy
import math

import utils.agv
from utils.doMap import wantMap
from utils.randomPositions import getRandomDestination
from utils.randomPositions import getRandomStart
from utils.randomPositions import getRandomTask

k = 0.1  # 转向修正系数
n = 9  # 前瞻步数
path = 'map.xlsx'


class AGV(object):
    def __init__(self, x, y, no, tasks, destination):
        self.x = x
        self.y = y
        self.no = no
        self.tasks = tasks
        self.destination = destination
        self.flag = False
        self.done_tasks = []
        self.start = [x, y]
        self.now_position = [x, y]
        self.agvList = [no]
        self.astar = Astar()  # 每一个AGV都有自己的Astar，用于自我的寻路工作，但是他们的地图是共享的
        self.result_paths = []
        self.conflict_list = [no]
        self.action_path = []
        self.singleDone = False
        self.path_no = 0
        self.mapList = []
        self.agvNowAction = []

    def addAgv(self, agvNo):
        self.agvList.append(agvNo)

    def removeAgv(self, agvNo):
        self.agvList.remove(agvNo)

    def changePosition(self, x, y):
        self.now_position = [x, y]

    def getTask(self):
        """获取agv当前需要执行的任务"""
        return self.tasks[0]

    def setmap(self, map):
        """设置当前地图"""
        #print('设置地图成功')
        self.astar.map = map

    def getStart(self):
        return self.done_tasks[-1]

    def finished_work(self):
        """此工作完成，需要将其转入到已完成列表中，并且将这个任务从任务列表中删除"""
        task = self.tasks[0]
        self.done_tasks.append(task)
        self.tasks.remove(task)

    def add_conflict_agv(self, no):
        """如果所指向的地方为AGV"""
        self.conflict_list.append(no)

    def addPath(self, path):
        """把最终路径加入到结果路径集合"""
        self.result_paths.append(path)


class Astar(object):
    """A star 类"""

    class Node(object):
        """节点类"""

        def __init__(self, x, y, parent_Node=None):
            self.x = x
            self.y = y
            self.parent_node = parent_Node
            self.G = 0
            self.H = 0

    def __init__(self):
        self.map = None
        self.openList = []
        self.closeList = []

    def is_in_openList(self, node):
        """检测节点node是否在openList中"""
        """如果该节点存在于openList中，那么返回该节点，否则返回False"""
        for n in self.openList:
            if node.x == n.x and node.y == n.y:
                return n

        return False

    def is_in_closeList(self, node):
        """判断该节点是否在closeList中"""
        """如果该节点存在于closeList中，那么返回该节点，否则返回False"""

        for n in self.closeList:
            if node.x == n.x and node.y == n.y:
                return n

        return False

    def minF(self):
        """寻找openList中F值最小的节点，并返回"""
        """使用最简单的排序算法找到F最小的节点"""

        minF = self.openList[0]
        for node in self.openList:
            if (minF.G + minF.H) > (node.G + node.H):
                minF = node

        return minF

    def is_obstacles(self, node):
        """判断当前节点是否是障碍物，也就是不可走"""
        if self.map[node.x][node.y].mapNum == -1:
            return True

        return False

    def is_agv(self, node, agv):
        """判断当前节点是否有AGV，是不可以通行的"""
        if self.map[node.x][node.y].mapAgvNo != -2 and agv.no != self.map[node.x][node.y].mapAgvNo:
            return True

        return False

    def over_bounder(self, node):
        """越界处理"""
        if node.x >= self.map.shape[0] or node.y >= self.map.shape[1] or node.x < 0 or node.y < 0:
            return True
        return False

    def is_product(self, node):
        """判断是否是货物"""
        if node.x == self.targetNode.x and node.y == self.targetNode.y:
            return True
        return False

    def searchHasObstals(self, node, agv):
        """进行探索，如果该节点不在openList中，或者不在closeList中，那么将其加入到openList，并且完成相应操作"""
        ## 找到货物的判断
        if self.is_product(node):
            print('找到货物')
            self.closeList.append(node)

        if self.is_in_closeList(node):
            return

        if self.is_in_openList(node):
            return

        if self.over_bounder(node):
            return

        if self.is_obstacles(node):
            return

        if self.is_agv(node, agv):
            return

        # 如果这个节点既不在closeList中，也不是不可达点
        parentNode = node.parent_node
        if node.x == parentNode.x or node.y == parentNode.y:
            # 如果两者的关系是上下的
            node.G = parentNode.G + 10
        else:
            node.G = parentNode.G + 14

        # 添加转向修正
        # node：下一节点
        # nowNode:当前节点
        # parentNode:当前节点的父节点
        nowNode = node.parent_node
        parentNode = nowNode.parent_node
        if parentNode is None:
            node.H = abs(self.targetNode.x - node.x) + abs(self.targetNode.y - node.y)
        else:
            if (nowNode.x - parentNode.x) * (node.y - parentNode.y) == (nowNode.y - parentNode.y) * (
                    node.x - parentNode.x):
                # 说明不是转弯，那么不进行修正
                node.H = abs(self.targetNode.x - node.x) + abs(self.targetNode.y - node.y)
            else:
                # 说明发生了转弯，那么要进行转向修正
                # print('处罚了转向修正，父节点({},{})，当前节点({},{})，下一节点({},{})'.format(parentNode.x,parentNode.y,nowNode.x,nowNode.y,node.x,node.y))
                node.H = abs(self.targetNode.x - node.x) + abs(self.targetNode.y - node.y) - k

        # 判断是否在openList中
        tem = self.is_in_openList(node)

        if tem:
            if tem.G > node.G:
                # 如果当前路径的最优，那么切换父节点
                tem.parent_node = parentNode
        else:
            self.openList.append(node)

    def search(self, node, agv):
        """进行探索，如果该节点不在openList中，或者不在closeList中，那么将其加入到openList，并且完成相应操作"""
        ## 找到货物的判断
        if self.is_product(node):
            print('找到货物')
            self.closeList.append(node)

        if self.is_in_closeList(node):
            return

        if self.is_in_openList(node):
            return

        if self.over_bounder(node):
            return

        if self.is_obstacles(node):
            return

        # if self.is_agv(node, agv):
        #     return

        # 如果这个节点既不在closeList中，也不是不可达点
        parentNode = node.parent_node
        if node.x == parentNode.x or node.y == parentNode.y:
            # 如果两者的关系是上下的
            node.G = parentNode.G + 10
        else:
            node.G = parentNode.G + 14

        # 添加转向修正
        # node：下一节点
        # nowNode:当前节点
        # parentNode:当前节点的父节点
        nowNode = node.parent_node
        parentNode = nowNode.parent_node
        if parentNode is None:
            node.H = abs(self.targetNode.x - node.x) + abs(self.targetNode.y - node.y)
        else:
            if (nowNode.x - parentNode.x) * (node.y - parentNode.y) == (nowNode.y - parentNode.y) * (
                    node.x - parentNode.x):
                # 说明不是转弯，那么不进行修正
                node.H = abs(self.targetNode.x - node.x) + abs(self.targetNode.y - node.y)
            else:
                # 说明发生了转弯，那么要进行转向修正
                # print('处罚了转向修正，父节点({},{})，当前节点({},{})，下一节点({},{})'.format(parentNode.x,parentNode.y,nowNode.x,nowNode.y,node.x,node.y))
                node.H = abs(self.targetNode.x - node.x) + abs(self.targetNode.y - node.y) - k

        # 判断是否在openList中
        tem = self.is_in_openList(node)

        if tem:
            if tem.G > node.G:
                # 如果当前路径的最优，那么切换父节点
                tem.parent_node = parentNode
        else:
            self.openList.append(node)

    def printOpenList(self):
        """打印openList中的内容"""
        path = []
        for i in range(len(self.openList)):
            path.append((self.openList[i].x, self.openList[i].y))
        return path

    def doOne(self, startNode, targetNode, agv, agv_list):
        """主要实现A-star的函数"""
        self.agv_list = agv_list
        self.startNode = Astar.Node(*startNode)
        self.targetNode = Astar.Node(*targetNode)

        if len(self.openList) == 0:
            """说明还未加入任何节点"""
            minF = self.startNode
        else:
            # 先判断目标节点在不在closeList中
            result_path = []
            tem = self.is_in_closeList(self.targetNode)
            returnTem = tem
            if tem:
                result_path.append([tem.x, tem.y])
                while tem.parent_node:
                    tem = tem.parent_node
                    result_path.append([tem.x, tem.y])
                result_path.reverse()
                results = result_path
                agv.result_paths.append(results)
                agv.finished_work()
                self.closeList.clear()
                self.openList.clear()
                print('agv{}完成了任务{},剩余任务为{}'.format(agv.no, [self.targetNode.x, self.targetNode.y], agv.tasks))
                return self.map, returnTem

            minF = self.minF()  # 从openList中找到F值最小的节点
            self.closeList.append(minF)  # 将minF加入到closeList中
            now_x = minF.x
            now_y = minF.y

            self.map[now_x][now_y].mapAgvNo = agv.no

            self.map[startNode[0]][startNode[1]].mapAgvNo = -2  # 修改AGV所处的上一个位置为0,表示可以行走
            self.openList.remove(minF)  # 将此点加入到closeList中

        # 依次搜索周围4个node
        self.searchHasObstals(Astar.Node(minF.x - 1, minF.y, minF), agv)  # 左
        self.searchHasObstals(Astar.Node(minF.x + 1, minF.y, minF), agv)  # 右
        self.searchHasObstals(Astar.Node(minF.x, minF.y - 1, minF), agv)  # 下
        self.searchHasObstals(Astar.Node(minF.x, minF.y + 1, minF), agv)  # 上
        return self.map, minF

    def star(self, startNode, targetNode, agv, agv_list):
        """主要实现A-star的函数"""
        self.agv_list = agv_list
        self.startNode = Astar.Node(*startNode)
        self.targetNode = Astar.Node(*targetNode)

        if len(self.openList) == 0:
            """说明还未加入任何节点"""
            minF = self.startNode
        else:
            # 先判断目标节点在不在closeList中
            result_path = []
            tem = self.is_in_closeList(self.targetNode)
            returnTem = tem
            if tem:
                result_path.append([tem.x, tem.y])
                while tem.parent_node:
                    tem = tem.parent_node
                    result_path.append([tem.x, tem.y])
                result_path.reverse()
                results = result_path
                agv.result_paths.append(results)
                agv.finished_work()
                self.closeList.clear()
                self.openList.clear()
                print('agv{}完成了任务{},剩余任务为{}'.format(agv.no, [self.targetNode.x, self.targetNode.y], agv.tasks))
                return self.map, returnTem

            minF = self.minF()  # 从openList中找到F值最小的节点
            self.closeList.append(minF)  # 将minF加入到closeList中
            now_x = minF.x
            now_y = minF.y

            self.map[now_x][now_y].mapAgvNo = agv.no

            self.map[startNode[0]][startNode[1]].mapAgvNo = -2  # 修改AGV所处的上一个位置为0,表示可以行走
            self.openList.remove(minF)  # 将此点加入到closeList中

        # 依次搜索周围4个node
        self.search(Astar.Node(minF.x - 1, minF.y, minF), agv)  # 左
        self.search(Astar.Node(minF.x + 1, minF.y, minF), agv)  # 右
        self.search(Astar.Node(minF.x, minF.y - 1, minF), agv)  # 下
        self.search(Astar.Node(minF.x, minF.y + 1, minF), agv)  # 上
        return self.map, minF


def init(task_num, map):
    """初始化任务"""
    start = getRandomStart(map)
    tasks = []
    for _ in range(TASK_NUM):
        tasks.append(getRandomTask(map))
    print('任务为：', tasks)
    destination = getRandomDestination(map)
    return start, tasks, destination


# 在这里执行多AGV多负载的任务执行
def run_this(now_map, agv_list):
    while 1:
        flag = True
        for agv in agv_list:

            if agv.flag:
                # 表明此AGV完成所有任务
                continue

            now_position = agv.now_position  # 获取每一个agv现在的位置
            task_position = agv.getTask()  # 获取该AGV目前的任务
            agv.setmap(now_map)  # 设置当前agv的地图
            map, position = agv.astar.star(now_position, task_position, agv, agv_list)  # 行走一步，利用的是同一个
            agv.now_position = [position.x, position.y]  # 修改AGV的当前位置信息
            now_map = map
            if len(agv.tasks) == 0:
                agv.flag = True

        for agv in agv_list:
            flag = agv.flag and flag
        if flag:
            break


def initAGV(agvNum, map, TASK_NUM):
    """初始化AGV"""
    agv_list = []
    starts = [[9, 3], [14, 3]]
    taskss = [[[13, 4]], [[3, 25]]]
    destinations = [[49, 1], [49, 2]]
    for no in range(agvNum):
        # start, tasks, destination = init(TASK_NUM, map)
        start = starts[no]
        tasks = taskss[no]
        print(tasks)
        destination = destinations[no]
        print('起点为：({},{})'.format(start[0], start[1]))
        x = start[0]
        y = start[1]
        agv = AGV(x, y, no, tasks, destination)  # 初始化一个AGV
        map[x][y].mapAgvNo = no
        agv_list.append(agv)

    return agv_list, map


def changePointToAction(agv_list):
    """将路径转化为agv行进方向"""
    for agv in agv_list:
        for path in agv.result_paths:
            action = utils.agv.agvAction(path)
            agv.action_path.append(action)


def goAction(action):
    """根据action行进"""
    if action == 'up':
        return [-1, 0]
    elif action == 'down':
        return [1, 0]
    elif action == 'left':
        return [0, -1]
    elif action == 'right':
        return [0, 1]
    elif action == 'turn around':
        return [0, 0]


def init_map(agv_list):
    """初始化AGV地图"""
    map = wantMap()
    for agv in agv_list:
        map[agv.start[0]][agv.start[1]].mapAgvNo = agv.no
    return map


def is_agv(node, map):
    """判断该位置是不是有AGV"""
    if map[node[0]][node[1]] >= 3:
        return True

    return False


def singleDone(agv):
    """单个AGV是否已经完成了自己的任务"""
    if len(agv.action_path) == 0:
        agv.singleDone = True
        print('==============agv{}完成了所有任务=============='.format(agv.no))
        if map[agv.now_position[0]][agv.now_position[1]] != 0:
            map[agv.now_position[0]][agv.now_position[1]] = 0


def allDone(agvlist):
    """判断是否所有AGV都完成寻路"""
    flag = True
    for agv in agvlist:
        if len(agv.action_path) == 0:
            flag = flag and True
        else:
            flag = flag and False
    return flag


def initAgvMapList(agv_list, map):
    for agv in agv_list:
        agv.mapList.append(map)
    return agv_list


def squeeze(agvList, n):
    """确定前瞻n步的行进内容"""
    for agv in agvList:
        if len(agv.action_path[0]) >= 9:
            del agv.action_path[0][9:]
        else:
            pass


def getMapList(agvList):
    import copy
    map0 = agvList[0].mapList[0]  # 获取初始地图
    n = len(agvList[0].action_path[0])  # 前瞻的步数
    # 初始操作
    map = copy.deepcopy(map0)
    for agv in agvList:
        agv.now_position = agv.result_paths[0][0]
        nowPosition = agv.now_position
        # 初始化map
        print('在map{}上添加位置{}，{}，为agv{}'.format(0, nowPosition[0], nowPosition[1], agv.no))
        map[nowPosition[0]][nowPosition[1]].mapAgvNo = agv.no
        map[nowPosition[0]][nowPosition[1]].mapAction = agv.action_path[0][0]
        # 覆盖原来的map0
        agv.mapList.clear()
        agv.mapList.append(map)

    for i in range(n - 1):
        map = copy.deepcopy(agvList[0].mapList[-1])
        for agv in agvList:
            nowPosition = agv.now_position  # 获得AGV的起始位置
            map[nowPosition[0]][nowPosition[1]].mapAgvNo = -2
            map[nowPosition[0]][nowPosition[1]].mapAction = None
            basePosition = goAction(agv.action_path[0][i])  # 获得basePosition
            newPosition = []
            newPosition.append(nowPosition[0] + basePosition[0])
            newPosition.append(nowPosition[1] + basePosition[1])
            # print(agv.action_path[0][i+1], '   ', basePosition)
            agv.now_position = newPosition  # 改变AGV的现在的位置
            print('在map{}上添加位置{}，{}，为agv{}'.format(i + 1, newPosition[0], newPosition[1], agv.no))
            map[newPosition[0]][newPosition[1]].mapAgvNo = agv.no
            map[newPosition[0]][newPosition[1]].mapAction = agv.action_path[0][i + 1]

        for agv in agvList:
            agv.mapList.append(map)


def chongtu(action, map, position):
    """判断该动作是否是发生冲突"""
    newPositioin = []
    if action == 'up':
        newPositioin.append(position[0] - 1)
        newPositioin.append(position[1])
        if map[newPositioin[0]][newPositioin[1]].mapAction == 'down' or map[newPositioin[0]][
            newPositioin[1]].mapAction == 'turn around':
            print('发生冲突，冲突AGV为{}和{}, agv{}的位置为({},{}), agv{}的位置为({},{}))'.format(map[position[0]][position[1]].mapAgvNo,
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 map[position[0]][position[1]].mapAgvNo,
                                                                                 position[0], position[1],
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 newPositioin[0], newPositioin[1]))
            # 返回冲突的AGV编号
            return map[newPositioin[0]][newPositioin[1]].mapAgvNo, map[position[0]][position[1]].mapAgvNo
    elif action == 'down':
        newPositioin.append(position[0] + 1)
        newPositioin.append(position[1])
        if map[newPositioin[0]][newPositioin[1]].mapAction == 'up' or map[newPositioin[0]][
            newPositioin[1]].mapAction == 'turn around':
            print('发生冲突，冲突AGV为{}和{}, agv{}的位置为({},{}), agv{}的位置为({},{}))'.format(map[position[0]][position[1]].mapAgvNo,
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 map[position[0]][position[1]].mapAgvNo,
                                                                                 position[0], position[1],
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 newPositioin[0], newPositioin[1]))
            # 返回冲突的AGV编号
            return map[newPositioin[0]][newPositioin[1]].mapAgvNo, map[position[0]][position[1]].mapAgvNo
    elif action == 'left':
        newPositioin.append(position[0])
        newPositioin.append(position[1] - 1)
        if map[newPositioin[0]][newPositioin[1]].mapAction == 'right' or map[newPositioin[0]][
            newPositioin[1]].mapAction == 'turn around':
            print('发生冲突，冲突AGV为{}和{}, agv{}的位置为({},{}), agv{}的位置为({},{}))'.format(map[position[0]][position[1]].mapAgvNo,
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 map[position[0]][position[1]].mapAgvNo,
                                                                                 position[0], position[1],
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 newPositioin[0], newPositioin[1]))
            # 返回冲突的AGV编号
            return map[newPositioin[0]][newPositioin[1]].mapAgvNo, map[position[0]][position[1]].mapAgvNo
    elif action == 'right':
        newPositioin.append(position[0])
        newPositioin.append(position[1] + 1)
        if map[newPositioin[0]][newPositioin[1]].mapAction == 'left' or map[newPositioin[0]][
            newPositioin[1]].mapAction == 'turn around':
            print('发生冲突，冲突AGV为{}和{}, agv{}的位置为({},{}), agv{}的位置为({},{}))'.format(map[position[0]][position[1]].mapAgvNo,
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 map[position[0]][position[1]].mapAgvNo,
                                                                                 position[0], position[1],
                                                                                 map[newPositioin[0]][
                                                                                     newPositioin[1]].mapAgvNo,
                                                                                 newPositioin[0], newPositioin[1]))
            # 返回冲突的AGV编号
            return map[newPositioin[0]][newPositioin[1]].mapAgvNo, map[position[0]][position[1]].mapAgvNo
    return None, None


def whoFar(agv1, agv2, agv1Position, agv2Position):
    """判断两个AGV谁离得比较远"""
    if hasattr(agv1, 'targetNode') is not True:
        agv1.targetNode = agv1.result_paths[0][-1]
    if hasattr(agv2, 'targetNode') is not True:
        agv2.targetNode = agv2.result_paths[0][-1]
    distance1 = math.sqrt((agv1.targetNode[0] - agv1Position[0]) ** 2 + (agv1.targetNode[1] - agv1Position[1]) ** 2)
    distance2 = math.sqrt((agv2.targetNode[0] - agv2Position[0]) ** 2 + (agv2.targetNode[1] - agv2Position[1]) ** 2)
    if distance1 > distance2:
        return agv1
    return agv2


# 在所有的AGV中寻找
def getAgv(agv_no, agvlist):
    """通过AGV编号找AGV"""
    for agv in agvlist:
        if agv.no == agv_no:
            return agv


def wait(agv1, agv2, agv1Position, agv2Position, map, n):
    """通过等待的方式解决"""
    # 通过等待有限步的方式解决冲突，预设等待步数为 3 步

    pass


def addTurn(agv1, agv2, agv1Position, agv2Position, map):
    """通过增加转向"""
    pass


def getPosition(map, agv):
    for i in range(map.shape[0]):
        for j in range(map.shape[1]):
            if map[i][j].mapAgvNo == agv.no:
                return i, j


def run(agv1, agv2, agv1Position, agv2Position, map, agvList):
    """绕行"""
    # 判断两者此时谁离目标远，谁就重新规划路径
    agv1 = getAgv(agv1, agvList)
    agv2 = getAgv(agv2, agvList)

    agv = whoFar(agv1, agv2, agv1Position, agv2Position)
    if agv1 == agv:
        gaiAgv = copy.deepcopy(agv1)
        otherAgv = copy.deepcopy(agv2)
        gaiPosition = agv1Position
    else:
        gaiAgv = copy.deepcopy(agv2)
        otherAgv = copy.deepcopy(agv1)
        gaiPosition = agv2Position

    print('重新规划路径的AGV为{}'.format(gaiAgv.no))

    # gaiAgv是需要重新寻址的AV，other是不需要重新寻址的AGV
    nowMap = copy.deepcopy(map)
    gaiAgvInitPosition = gaiAgv.result_paths[0][0]  # 获得需要重新规划路径的AGV的初始位置
    # 设置新的地图信息
    nowMap[gaiAgvInitPosition[0]][gaiAgvInitPosition[1]].mapAgvNo = gaiAgv.no
    nowMap[gaiPosition[0]][gaiPosition[1]].mapAgvNo = -2
    # 找到此时不需要修改AGV的坐标，然后重新开始规划路径
    x, y = getPosition(map, otherAgv)
    print('不动的AGV的位置为',x,y)
    nowMap[x][y].mapAgvNo = otherAgv.no
    gaiAgv.now_position = gaiAgvInitPosition
    gaiAgv.tasks.append(gaiAgv.result_paths[0][-1])
    for i in range(nowMap.shape[0]):
        for j in range(nowMap.shape[1]):
            if nowMap[i][j].mapAgvNo == otherAgv.no:
                print(i,j)
    # 开始规划AGV路径
    while 1:
        now_position = gaiAgv.now_position  # 获取每一个agv现在的位置
        task_position = gaiAgv.getTask()  # 获取该AGV目前的任务
        gaiAgv.setmap(nowMap)  # 设置当前agv的地图
        maps, position = gaiAgv.astar.doOne(now_position, task_position, gaiAgv, [gaiAgv])  # 行走一步，利用的是同一个
        gaiAgv.now_position = [position.x, position.y]  # 修改AGV的当前位置信息
        nowMap = maps
        if position.x == task_position[0] and position.y == task_position[1]:
            break
    # 规划AGV路径完成
    print('规划AGV路径完成')
    # 将重新规划路径的AGV的路径转为方向

    gaiAgv.result_paths.pop(0)
    changePointToAction([gaiAgv])
    gaiAgv.action_path.pop(0)
    print(gaiAgv.action_path)
    print(gaiAgv.result_paths[0])
    squeeze([gaiAgv], 9)
    agvList[gaiAgv.no] = gaiAgv

    getMapList(agvList)

    return agvList


def solveConflict(agv1, agv2, agv1Position, agv2Position, map, n, agvList):
    """
    解决AGV1和AGV2之间的冲突\n
    有三种解决冲突的方式：\n
    1、增加等待，已解决冲突（等待三步） 如果存在其他AGV此时存储的地图链表不够三步的怎么处理 \n
    2、增加转向\n
    3、绕行

    n：表示第几步冲突
    agv1、agv2表示冲突AGV
    agv1Position、agv2Position表示AGV1和AGV2的位置
    """
    # time1 = wait(agv1, agv2, agv1Position, agv2Position, map, n)
    # time2 = addTurn(agv1, agv2, agv1Position, agv2Position, map)
    print('第{}步冲突'.format(n))
    agvList = run(agv1, agv2, agv1Position, agv2Position, map, agvList)
    return agvList


def hasConflict(map0, n, agvList):
    width = map0.shape[0]
    height = map0.shape[1]
    flags = False
    for i in range(width):
        for j in range(height):
            if map0[i][j].mapAgvNo != -2:
                # 说明此处有AGV，那么可能发生冲突
                position = [i, j]
                action = map0[i][j].mapAction  # 获取动作
                agv1, agv2 = chongtu(action, map0, position)  # 得到冲突的AGV编号
                if agv1 is not None and agv2 is not None and agv1 != agv2:  # 有冲突的话
                    basePosition = goAction(action)
                    agv1Position = [basePosition[0] + position[0], basePosition[1] + position[1]]
                    agv2Position = position
                    agv_list = solveConflict(agv1, agv2, agv1Position, agv2Position, map0, n, agvList)  # 解决冲突
                    flags = True
                    return agv_list, flags

    return agvList, flags


def ifConflict(agv_list):
    agv = agv_list[0]
    flag = False
    for i in range(len(agv.mapList)):
        map0 = agv.mapList[i]
        agv_list, flags = hasConflict(map0, i, agv_list)
        if flags:
            flag = True
            break
    return agv_list, flag


if __name__ == "__main__":
    TASK_NUM = 1  # 任务数量
    AGV_NUM = 2  # AGV数量
    N = 9  # 前瞻步数
    initMap = wantMap()  # 获得初始化地图
    agv_list, map = initAGV(AGV_NUM, initMap, TASK_NUM)  # 初始化AGV列表以

    agv_list = initAgvMapList(agv_list, map)  # 将地图信息加入到AGV地图链表中，作为map0
    agvList = agv_list
    run_this(map, agv_list)  # AGV按照顺序执行
    for agv in agv_list:
        print(agv.result_paths)
    changePointToAction(agv_list)  # 根据节点信息为AGV方向信息
    # 根据前瞻步数去压缩每一个agv的行进方向，也就是说每一个agv的action中只存储9个
    squeeze(agv_list, n)
    for agv in agv_list:
        print(agv.action_path)
    # 根据当前9步去加载每一步的地图信息，并且将他们同时存于agv的mapList中，不考虑冲突
    getMapList(agv_list)
    # 根据mapList判冲突
    flag = True
    while flag:
        agv_list, flag = ifConflict(agv_list)
