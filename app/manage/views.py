from .import manage
from ..models import grade_info, class_info, job_submission, teacher, user
from .. import db
from flask_paginate import Pagination, get_page_parameter
from flask import render_template, redirect, flash, url_for, request
from ..models import grade_info, class_info, student, teacher, teaching_information,representative, user,subject
from .forms import students_add, teacher_add, teacher_add_all,subjects
from .. import db
import pandas as pd
from flask_login import current_user
from sqlalchemy import func


@manage.route("/", methods=["POST", "GET"])
def personnel_managementmanage():
    if current_user.role.role=="admin":
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
                teacher_.subject = subjects[int(request.values.get("subject"))-1][1]
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
            count=0
            for index, i in df.iterrows():
                if not i['学号'] and i['姓名'] and i['班级'] :
                    continue
                user_=user.query.filter(user.username==i["学号"]).first()
                if user_:
                    continue
                else:
                    stu = student()
                    adduser = user()
                    adduser.username = i["学号"]
                    adduser.realname = i["姓名"]                    
                    adduser.role_id = 4
                    adduser.password="123456"
                    stu.number = i["学号"]
                    stu.name = i["姓名"]
                    class_= db.session.query(class_info).filter_by(class_name=i["班级"]).first()
                    if class_:
                        stu.class_id =class_.id
                    else:
                        flash("错误的班级名称")
                        continue
                    count+=1
                    db.session.add(stu)
                    db.session.add(adduser)
                    db.session.flush()
            flash("成功导入学生%s名" %count)
        if us1.submit.data and us1.validate_on_submit():
            file = request.files['file'].read()
            df = pd.read_excel(file)
            for index, i in df.iterrows():
                n=0
                if i["身份证号"] and i["姓名"]:
                    if  db.session.query(user).filter_by(realname= i["姓名"],id_number=i["身份证号"]).first():
                        flash("当前用户已存在")
                    else:
                        user_ = user(realname = i["姓名"], id_number = i["身份证号"], password="123456",role_id = 1)
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
        search = False  # 分页切片，flask_paginate模块实现
        q = request.args.get('q')
        if q:
            search = True
        page = request.args.get(get_page_parameter(), type=int, default=1)
        start = (page-1)*10
        end =page*10
        user_ = user.query.order_by(user.role_id).slice(start,end)
        pagination = Pagination(page=page, total=len(user.query.all()), bs_version=4, search=search, record_name='user_')
        return(render_template("manage/user_manage.html", u=u, us=us, us1=us1, user=user_,pagination=pagination))
    elif current_user.role.role=="teacher":
        class_=current_user.teacher.teaching_information.filter(teaching_information.subject!="master_teacher").order_by(teaching_information.class_id.asc())
        return(render_template("manage/manage_student.html",class_=class_, job_submission=job_submission()))

@manage.route("/teacher/<id>", methods =["POST","GET"])
def teacher_manage(id):
    teacher_ = user.query.filter_by(id=id).first()
    g = grade_info.query.all()
    c = class_info.query.all()
    t=teaching_information.query.filter(teaching_information.teacher_id==teacher_.teacher.id)
    class_=[]
    for i in t.all():
        if i.class_id not in class_:
            class_.append(i.class_id)
    if request.method=="POST":
        id=request.form.get("class_master")
        class__ = request.form.getlist("cla")

        for i in t.all():
            if str(i.class_id) not in class__:                
                db.session.delete(i)
        for i in class__:
            print(i,class_)
            print(i not in class_)
            if int(i) not in class_:
                t2=teaching_information(subject=teacher_.teacher.subject,class_id=i,teacher_id=teacher_.teacher.id)
                db.session.add(t2)
        if id:
            appointed = class_info.query.filter(class_info.class_master==teacher_.teacher.id).first()
            new=class_info.query.filter(class_info.id==id).first()
            if new:
                if appointed:
                    if appointed.id != new.id:
                        appointed.class_master=None
                        teachinfor=teaching_information.query.filter(teaching_information.class_id==appointed.id).filter(teaching_information.teacher_id==teacher_.teacher.id).filter(teaching_information.subject=="master_teacher").first()
                        db.session.delete(teachinfor)
                new.class_master = teacher_.teacher.id
                t1=teaching_information(subject="master_teacher",class_id=new.id,teacher_id=teacher_.teacher.id)
                db.session.add(t1)  
        db.session.flush()                
        db.session.commit()
        
        return(redirect(url_for("main.index")))
    return(render_template("manage/teacher.html",teacher=teacher_,teaching_information=class_ ,g=g,c=c))


@manage.route("/student/<id>", methods =["POST","GET"])
def student_overview(id):
    stu=student.query.filter(student.id==id).first()
    jobs=job_submission.query.filter(job_submission.student==id)
    aver=jobs.with_entities(func.avg(job_submission.mark)).scalar()
    if not aver:
        aver=0
    return(render_template("manage/stu_personal_info.html",stu=stu,jobs=jobs,avg=aver,job_submission=job_submission))

@manage.route("/class/<id>", methods =["POST","GET"])
def class_overview(id):
    cla=class_info.query.filter(class_info.id==id).first()
    return(render_template("manage/class_info.html",cla=cla))

@manage.route("/representative/", methods =["POST","GET"])
def representative_overview():
    pass
