"""视图文件，对请求进行处理，返回视图文件（网页模板）"""
 # -*-coding:utf-8-*-
import os
from flask.helpers import url_for
from sqlalchemy.sql.elements import Null
from .import main
from flask import render_template, redirect, flash, send_from_directory, request
from ..models import grade_info, class_info, student, teacher, teaching_information, user,subject
from .forms import school_settings
from .. import db


@main.route("/index", methods=["POST", "GET"])
def index():
    return(render_template("index.html"))


@main.route("/teaching", methods=["POST", "GET"])
def teaching():
    return(render_template("index.html"))




@main.route("/search/<ob>", methods=["POST", "GET"])
def search(ob):
    return(str(ob))


@main.route("/test", methods=["POST", "GET"])
def test():
    u = user(username = "test",password = "123",role_id = "1")
    db.session.add(u)
    db.session.commit()
    return(render_template("test.html"))


@main.route("/")
def root():
    return(redirect("/auth/"))


@main.route("/structure", methods=["POST", "GET"])  # 批量添加数据的方法案例, 设置年级和班级
def structure():   
    school = school_settings()
    if school.submit1.data and school.validate_on_submit():  # 组织结构设置
        name = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        sch = ["小", "初", "高"]
        db.session.commit()
        grade = db.session.query(grade_info).all()
        class_ = class_info.query.all()
        for i in class_:
            db.session.delete(i)
        db.session.commit()
        for i in grade:
            db.session.delete(i)
        db.session.commit()
        for i in range(school.grade.data):
            grade = grade_info(grade_name=sch[school.school.data - 1] + name[i])  # 批量添加数据，不能使用类似grade =grade_info(),grade.grade_name=xxx的方法，该方法会造成只添加最后一个条数据
            db.session.add(grade)
            db.session.flush()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("操作失败，请重试")
            for j in range(school.class_num.data):
                class_ = class_info(class_name= grade.grade_name + "(%s)" % (j + 1), grade_id = grade.id)
                db.session.add(class_)
                db.session.flush()
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    flash("操作失败，请重试")
        flash("操作成功，你已成功添加%s个年级和%s个班级" % (i+1, (i+1) * (j+1)))
    g = grade_info.query.all()
    c = class_info.query.all()
    
    return(render_template("structure.html", school=school, g=g, c=c))


@main.route("/download/<path:filename>",methods=["POST","GET"])
def download(filename):
    
    dir = os.getcwd()
    dir =os.path.join(dir,"app\\static\\file\\")    
    return send_from_directory(dir,filename, as_attachment=True)

