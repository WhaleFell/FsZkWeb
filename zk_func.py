'''
Author: whalefall
Date: 2021-03-20 16:37:34
LastEditTime: 2021-07-12 09:52:51
Description: 中考报名网站请求方法库
'''
import base64
# 懒得研究/复写他的加密算法 直接用execjs模拟
import configparser
import datetime
import hashlib
import os
import random
import re
import sys
import threading
# from Crypto.Cipher import AES # 没能力复写JS加密 弃用
import time
from ast import literal_eval  # 字符串列表转列表
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import execjs
# 验证码
import pytesseract
import requests
from lxml import etree
from PIL import Image
import traceback
# import pymysql
import pymongo

class Encrypt(object):
    '''
    处理加密类
    '''

    def __init__(self):
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "EncryptJS.js"),
                  mode="r") as js:
            jsContent = js.read()
        self.ctx = execjs.compile(jsContent)

    def userid(self, userid):
        '''传入账号,返回加密'''
        return self.ctx.call("encryptByDES", userid, "AGH123OL")

    def pwd(self, pwd):
        '''传入密码,返回加密'''
        return self.ctx.call("hex_md5", pwd)


class Zkweb(object):
    '''
    请求的类
    '''
    # 初始化各种属性

    def __init__(self):
        self.header = {
            "User-Agent":
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366 MicroMessenger/6.7.3(0x16070321) NetType/WIFI Language/zh_CN",
            "Accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Cookie: SESSION=a02ab646-9f8a-4755-9abb-f722d6fb1676; name=value; JSESSIONID=value,
            "Host": "exam.edu.foshan.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://exam.edu.foshan.gov.cn/iexamfs/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        self.sessions = requests.session()  # 带cookies的请求

        self.code = None  # 验证码内容
        self.index_url = None
        # self.count = 0  # 失败计数

        self.myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = self.myclient["zk"]
        self.mycol = mydb["zk_student"]


    # 获取验证码地址
    def getCode(self):
        url = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginAction.action"
        try:
            resp = self.sessions.get(url, headers=self.header, timeout=14)
            html = etree.HTML(resp.text)
            code = html.xpath(
                "/html/body/form/table/tr/td[2]/table/tr[4]/td/table/tr/td/table/tr[3]/td[2]/img/@src"
            )[0]
            code_url = "https://exam.edu.foshan.gov.cn/iexamfs/" + code
            # print("验证码地址:", code_url)
            return code_url
        except Exception as e:

            print("获取验证码地址时发送异常:", traceback.format_exc())
            raise requests.ConnectionError

    # 下载验证码 返回二进制信息
    def downloadCode(self):
        '''
        下载验证码,返回二进制信息
        '''
        code_url = self.getCode()
        if code_url == None:
            pass
        else:
            try:
                resp = self.sessions.get(
                    code_url, headers=self.header, timeout=14)
                # 验证码内容
                self.code = resp.content
                return True
            except Exception as e:
                print("下载验证码失败! URL:%s" % (code_url))
                # return False
                raise requests.ConnectionError
            finally:
                resp.close()
    # 验证码识别部分

    def checkCode(self):
        if self.downloadCode():
            image = self.dispose_code()  # 效果最好的方案
            code = pytesseract.image_to_string(image)
            # 去掉非法字符，只保留字母数字
            textCode = re.sub("\W", "", code)
            # print("识别到的验证码:", textCode)

            # 验证码为空 重试
            if textCode == "":
                return False

            return textCode

        else:
            return False

    # 美化验证码3 个人感觉效果最好的方案了
    def dispose_code(self):
        # 读取二进制图片
        img = Image.open(BytesIO(self.code))

        def binarizing(img, threshold):
            """传入image对象进行灰度、二值处理"""
            img = img.convert("L")  # 转灰度
            pixdata = img.load()
            w, h = img.size
            # 遍历所有像素，大于阈值的为黑色
            for y in range(h):
                for x in range(w):
                    if pixdata[x, y] < threshold:
                        pixdata[x, y] = 0
                    else:
                        pixdata[x, y] = 255
            return img

        img = binarizing(img, 225)
        """传入二值化后的图片进行降噪"""
        pixdata = img.load()
        w, h = img.size
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                count = 0
                if pixdata[x, y - 1] > 245:  # 上
                    count = count + 1
                if pixdata[x, y + 1] > 245:  # 下
                    count = count + 1
                if pixdata[x - 1, y] > 245:  # 左
                    count = count + 1
                if pixdata[x + 1, y] > 245:  # 右
                    count = count + 1
                if pixdata[x - 1, y - 1] > 245:  # 左上
                    count = count + 1
                if pixdata[x - 1, y + 1] > 245:  # 左下
                    count = count + 1
                if pixdata[x + 1, y - 1] > 245:  # 右上
                    count = count + 1
                if pixdata[x + 1, y + 1] > 245:  # 右下
                    count = count + 1
                if count > 4:
                    pixdata[x, y] = 255
        # img.show()
        return img

    # 登录部分
    def login(self, code, userid, pwd="fb45cf48a07a7948bcd029c24c011720"):
        '''
        传入账号,密码(可不传),验证码
        '''
        url = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginSuccessAction.action"

        data = {
            "ksLoginUsername": "ksno",
            "userid": Encrypt().userid(userid),
            "login.logintype": "ks",
            # "keyvalue": Encrypt().pwd(pwd),
            "keyvalue": pwd,
            "rand": code,
        }

        # print(data)

        try:
            resp = self.sessions.post(
                url, data=data, headers=self.header, timeout=14)
        except:
            print("请求登录接口错误?")
            raise requests.ConnectionError
            # return "apiError"
        finally:
            resp.close()

        # 登录时的错误

        # print(resp.text)
        if "输入的验证码错误" in resp.text:
            # print("验证码识别有误:%s" % (code))
            return False

        # 可能账号密码不存在之类的
        elif "[规则]登录失败！" in resp.text:

            print("%s登录受限!" % (userid))

            return "LoginError"

        elif "登录失败，请核对您的用户名和密码！" in resp.text:
            print("账号(%s)密码(%s)有误!" % (userid, pwd))
            return "PwdError"

        elif "账号已被锁定，请在5分钟后进行尝试。" in resp.text:
            print("[Suc]账号(%s)已被锁定!" % (userid))
            return "Locking"

        else:
            print("可能登录成功?")
    def writeMongoDB(self,id):
        timestamp = int(time.time())
        '''
        储存账号锁定的时间.并更新各账号.
        写入 monggoDB,传入id,自动生成时间戳.
        {"_id":"账号,插入时随之更新time","time":锁定时间戳}
        '''
        try:
            self.mycol.replace_one({"_id": id}, mydict, upsert=True)

        except Exception as e:
            print("写入MongoDB数据库出现问题", e)
        finally:
            self.myclient.close()

    def main(self,id):
        count = 0  # 计数器
        try:
            bot = Zkweb()
            code = bot.checkCode()
            if code == False:
                # print("id:%s验证码为空!" % (id))
                self.main(id)
            result = bot.login(code, id)
            if result == False:
                # print("%s验证码识别错误%s" % (id, code))
                self.main(id)
            if result == "PwdError":
                count += 1
                self.main(id)
            if result == "Locking":
                if count == 0:
                    # 第一次请求就锁定的账号入第一次就锁定库
                    print("账号%s第一次请求就锁定" % (id))
                    id_queue.put(id)

                    return "oneLock"
                    # return
                # 账号成功锁定,写入数据库
                self.writeMongoDB(id)
                return
            else:
                return
        except Exception as e:
            print("[INFO]发生异常别怕,递归直至成功", e)
            self.main(id)

if __name__ == "__main__":

    # print(Encrypt().pwd("@123456Aa"))
    Zkweb().getCode()
