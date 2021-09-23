"""视图文件，对请求进行处理，返回视图文件（网页模板）"""
 # -*-coding:utf-8-*-
 
import os
from .import main
from flask import render_template, redirect, flash, send_from_directory, request
from ..models import grade_info, class_info, student, teacher, user
from .forms import school_settings, students_add, teacher_add, teacher_add_all, students_add
from .. import db
import time
import pandas as pd
from flask_paginate import Pagination, get_page_parameter

@main.route("/index", methods=["POST", "GET"])
def index():
    return(render_template("index.html"))


@main.route("/teaching", methods=["POST", "GET"])
def teaching():
    return(render_template("index.html"))


@main.route("/manage", methods=["POST", "GET"])
def manage():
    u = teacher_add()
    us = students_add()
    us1 = teacher_add_all()
    if u.submit2.data and u.validate_on_submit():  # 添加教师用户   
        if db.session.query(user).filter_by(realname=u.username.data,id_number=u.id_number.data).first():
            flash("当前用户已存在")
        else:
            user_ = user(realname = u.username.data, id_number = u.id_number.data, role_id = 1)
            teacher_ = teacher()
            db.session.add(user_)
            db.session.flush()
            db.session.commit()
            teacher_.subject = u.subject.data
            teacher_.user_id = user_.id
            db.session.add(teacher_)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("添加错误，请重试")
    if us.submit3.data and us.validate_on_submit():
        file = request.files['file'].read()
        df = pd.read_excel(file)
        for index, i in df.iterrows():
            stu =student()
            stu.number = i["学号"]
            stu.name = i["姓名"]
            print(i["班级"])
            class_= db.session.query(class_info).filter_by(class_name=i["班级"]).first()
            if class_:
                stu.class_id =class_.id
            else:
                flash("错误的班级名称")
                break
            db.session.add(stu)
            db.session.flush()
        flash("成功导入学生%s名" %len(df))
    if us1.submit.data and us1.validate_on_submit():
        file = request.files['file'].read()
        df = pd.read_excel(file)
        for index, i in df.iterrows():
            n=0
            if i["身份证号"] and i["姓名"]:
                if  db.session.query(user).filter_by(realname= i["姓名"],id_number=i["身份证号"]).first():
                    flash("当前用户已存在")
                else:
                    user_ = user(realname = i["姓名"], id_number = i["身份证号"], role_id = 1)
                    teacher_ = teacher()
                    db.session.add(user_)
                    db.session.flush()
                    db.session.commit()
                    teacher_.subject = i["学科"]
                    teacher_.user_id = user_.id
                    db.session.add(teacher_)
                    try:
                        n+=1
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                        flash("添加错误，请重试")
        flash("成功导入教师%s名" %n)    
    db.session.commit()
    t = teacher.query.all()
    search = False  # 分页切片，flask_paginate模块实现
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page-1)*8
    end =page*8
    user_ = user.query.slice(start,end)
    pagination = Pagination(page=page, total=len(user.query.all()), bs_version=4, search=search, record_name='user_')
    return(render_template("user_manage.html", u=u, us=us, us1=us1, user=user_,pagination=pagination))


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
                class_ = class_info(class_name= grade.grade_name + "(%s)" % (j + 1), grade_name = grade.grade_name)
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

