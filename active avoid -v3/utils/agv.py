# -*- coding: utf-8 -*-
"""
@Time ： 2021/12/21 16:42
@Auth ： Mr.Hu
@File ：agv.py
@IDE ：PyCharm
@Motto：ABC(Always Be Coding)
对于AGV动作 go back left right turn_around
    go：向上走
    back：向下走
    left：向左走
    right：向右走
    turn_around：AGV朝向改变
"""


def agvAction(path):
    if len(path)>2:
        actions = agvActions(path)
    else:
        actions = []
        actions.append(getAction1(path[0], path[1]))
    return actions

def agvActions(path):
    """根据当前路径形成AGV的动作列表"""
    # 单独处理第一步
    actions = []
    first_step = path[0]
    second_step = path[1]
    action = getAction1(first_step, second_step)
    actions.append(action)

    # 统一处理后面每一步
    parent_step = path[0]
    now_step = path[1]
    next_step = path[2]
    count = 2

    while now_step != path[-1]:
        action = getAction2(parent_step, now_step, next_step)
        actions.append(action)
        if action == 'turn around':
            action = getAction1(now_step, next_step)
            actions.append(action)
        parent_step = now_step
        now_step = next_step
        if now_step == path[-1]:
            break
        count += 1
        next_step = path[count]

    return actions


def isEquals(a, b, c):
    if a == b == c:
        return True
    else:
        return False


def getAction2(parent_step, now_step, next_step):
    """判断action"""
    # 如果三者的横坐标或者纵坐标相等，那么没有转向发生，所以只需要使用now_step和next_step
    if isEquals(parent_step[0], now_step[0], next_step[0]) or isEquals(parent_step[1], now_step[1], next_step[1]):
        # 没有转弯
        action = getAction1(now_step, next_step)
        return action
    else:
        # 有转弯发生
        action = 'turn around'
        return action


def getAction1(first_step, second_step):
    """根据两步判断是否是go  or  back"""
    f_x = first_step[0]
    f_y = first_step[1]
    s_x = second_step[0]
    s_y = second_step[1]

    if f_x == s_x:  # left、right
        if f_y > s_y:
            return 'left'
        else:
            return 'right'

    if f_y == s_y:  # up、down
        if f_x < s_x:
            return 'down'
        else:
            return 'up'
