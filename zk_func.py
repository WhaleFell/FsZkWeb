'''
Author: whalefall
Date: 2021-03-20 16:37:34
LastEditTime: 2021-07-10 20:10:35
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


class Encrypt:
    def __init__(self):

        # 加密的js文件

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                               "EncryptJS.js"),
                  mode="r") as js:
            jsContent = js.read()

        self.ctx = execjs.compile(jsContent)

    def userid(self, userid):

        return self.ctx.call("encryptByDES", userid, "AGH123OL")

    def pwd(self, pwd):

        return self.ctx.call("hex_md5", pwd)


# 从这里开始


class Zkweb:

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
        self.count = 0  # 失败计数

    # 获取验证码地址
    def getCode(self):
        url = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginAction.action"
        try:
            resp = self.sessions.get(url, headers=self.header)
            # print(resp.text)
            html = etree.HTML(resp.text)
            code = html.xpath(
                "/html/body/form/table/tr/td[2]/table/tr[4]/td/table/tr/td/table/tr[3]/td[2]/img/@src"
            )[0]
            code_url = "https://exam.edu.foshan.gov.cn/iexamfs/" + code
            # print("验证码地址:", code_url)
            return code_url
        except Exception as e:

            print("页面验证码获取失败 原因:")

            try:
                if "系统例行维护" in resp.text:
                    print("中考报名系统晚上22:30至次日08:30暂停服务!")
                    sys.exit()
            except Exception as er:
                print("错误信息:%s" % (er))
                time.sleep(5)

            return None

        finally:
            resp.close()

    # 下载验证码 返回二进制信息
    def downloadCode(self):
        code_url = self.getCode()
        if code_url == None:
            pass
        else:
            try:
                resp = self.sessions.get(code_url, headers=self.header)

                # 验证码内容
                self.code = resp.content

                return True
            except Exception as e:
                print("下载验证码失败! URL:%s" % (code_url))
                return False
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

    # 登录部分 并获取主页
    def login(self, code, userid,pwd="fb45cf48a07a7948bcd029c24c011720"):
        '''
        传入账号,密码(可不传)
        '''
        url = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginSuccessAction.action"

        data = {
            "ksLoginUsername": "ksno",
            "userid": Encrypt().userid(userid),
            "login.logintype": "ks",
            # "keyvalue": Encrypt().pwd(pwd),
            "keyvalue":pwd,
            "rand": code,
        }

        # print(data)

        try:
            resp = self.sessions.post(url, data=data, headers=self.header)
        except:
            print("请求登录接口错误?")
            return "apiError"
        finally:
            resp.close()

        # 登录时的错误

        # print(resp.text)
        if "输入的验证码错误" in resp.text:
            print("验证码识别有误:%s" % (code))
            return False

        # 可能账号密码不存在之类的
        elif "[规则]登录失败！" in resp.text:

            print("%s登录受限!" % (userid))
            self.count += 1
            if self.count >= 10:
                print("账户(%s)可能被限制超过10次 请换ip" % (userid))
                return "resqError"

            return False

        elif "登录失败，请核对您的用户名和密码！" in resp.text:
            print("账号(%s)密码(%s)有误!" % (userid, pwd))
            return "PwdError"

        elif "账号已被锁定，请在5分钟后进行尝试。" in resp.text:
            print("[Suc]账号(%s)已被锁定!" % (userid))
            return "Locking"

        else:
            print("可能登录成功?")

            try:
                # 获取主页加密

                html = etree.HTML(resp.text)
                # 更新获取主页 2021.4.4
                self.index_url = html.xpath("/html/body/div[4]/a[1]/@href")[0]
                print("主页链接:%s" % (self.index_url))
                return True

            except:
                print("获取主页链接失败", resp.text)
                with open(os.path.join(
                        os.path.abspath(os.path.dirname(__file__)),
                        "error//%s %s.html" %
                    (userid, time.strftime("%H-%M-%S", time.localtime()))),
                          mode="w",
                          encoding="gb2312") as f:

                    f.write(resp.text)

                    print("错误主页%s已下载" % (userid))

                return "Error"


if __name__ == "__main__":
    
    print(Encrypt().pwd("@123456Aa"))