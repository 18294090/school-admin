"""视图文件，对请求进行处理，返回视图文件（网页模板）"""
from .import main
from flask import render_template

@main.route("/index", methods=["POST", "GET"])
def index():
	return(render_template("index.html")) 


@main.route("/teaching", methods=["POST", "GET"])
def teaching():
	return(render_template("index.html")) 

@main.route("/manage", methods=["POST", "GET"])
def manage():
	return(render_template("index.html"))

@main.route("/search/<ob>", methods=["POST", "GET"])
def search(ob):
	return(ob)

@main.route("/", methods=["POST", "GET"])
def login():  # 处理登录逻辑,下拉列表选择用户
    classes = class_info.query.filter_by(status=True).all()
    form = loginform()
    form1 = userlogin()
    if classes:
        form.class_name.choices = [v.name for v in classes]
        form.stuname.choices = [(v.school_num, v.name) for v in classes[0].students]
    if form.validate_on_submit():
        stuname = form.stuname.data
        password = form.password.data
        login_check = students.query.filter_by(school_num=stuname).first().username
        if login_check.id and login_check.password == password:
            session["userid"] = login_check.id
            return(redirect(url_for("main.index")))
        else:
            return(render_template("test.html", x=session["userid"]))
    if form1.validate_on_submit():
        username = form1.username.data
        password = form1.password.data
        login_check = user.query.filter_by(username=username).first()
        if login_check and login_check.password == password:
            session["userid"] = login_check.id
            return(redirect(url_for("main.index")))
        else:
            return(render_template("test.html", x=session["userid"]))
    return(render_template("login.html", form=form, form1=form1))