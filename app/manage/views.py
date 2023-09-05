from .import manage
from .. import db
from flask_paginate import Pagination, get_page_parameter
from flask import render_template, redirect, flash, url_for, request,send_from_directory,jsonify
from ..models import role,grade_info, class_info,class_student, student, teacher, teaching_information,representative, user,subject,Permission
from .forms import students_add, teacher_add, teacher_add_all,subjects
from .. import db
from ..decorators import permission_required
import pandas as pd
from flask_login import current_user,login_required
from sqlalchemy import func
import os
import datetime

@manage.route("/people_management/", methods=["POST", "GET"])
@login_required 
@permission_required(Permission.admin)
def people_management():
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
            count1=0
            count2=0
            count3=0
            for index, i in df.iterrows():
                if not i['学号'] and i['姓名'] and i['班级'] :
                    flash("第%s行信息不全" %index )
                    continue 
                num=i["学号"]
                if not isinstance(num, str):
                    num=str(num)
                while len(num)<10:
                    num="0"+num
                stu=student.query.filter(student.number==num).first()
                class_= db.session.query(class_info).filter_by(class_name=i["班级"]).first()
                if stu:
                    count1+=1
                    pass
                else:
                    stu = student()
                    stu.number = num
                    stu.name = i["姓名"]                
                    if i["性别"] in ["男","女"]:
                        stu.gender=i["性别"]
                    else:
                        stu.gender=""                    
                    if class_:
                        stu.class_id =class_.id
                    else:
                        flash("错误的班级名称%s" %i["班级"])
                        continue
                    count+=1
                    db.session.add(stu)
                    db.session.flush()
                c_s=class_student.query.filter(class_student.class_id==class_.id,class_student.student_id==stu.id).first()
                if not c_s:
                    count2+=1
                    c_s=class_student(class_id=class_.id,student_id=stu.id)
                    db.session.add(c_s)
                    db.session.flush()
                else:
                    c_s.class_id=class_.id
                    db.session.flush()
                    count1+=1
            if count1:    
                flash("%s名学生已存在，请检查文件"%count1)
            if count2:
                flash("%s名学生分班信息已导入"%count2)
            if  count:
                flash("成功导入学生%s名" %count)
            if count3:
                flash("%s名学生已存在，已更新分班信息"%count3)
            try:                                                                 
                db.session.commit()               
            except Exception:
                db.session.rollback()
                flash("添加错误，请重试")
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
                        db.session.flush()
                        n+=1
            try:
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
        user_  =db.session.query(user).join(role).filter(role.permissions.op('&')(Permission.job_publish) == Permission.job_publish).order_by(user.role_id).slice(start,end)
        pagination = Pagination(page=page, total=len(user.query.all()), bs_version=4, search=search, record_name='user_')
        return(render_template("manage/user_manage.html", u=u, us=us, us1=us1, user=user_,pagination=pagination))
    elif current_user.role.role=="teacher":
        class_=current_user.teacher.teaching_information.filter(teaching_information.subject!="master_teacher").order_by(teaching_information.class_id.asc())
        return(render_template("manage/manage_student.html",class_=class_, job_submission=job_submission()))

@manage.route("/teacher/<id>", methods =["POST","GET"])
@login_required 
@permission_required(Permission.admin)
def teacher_manage(id):
    teacher_ = user.query.filter_by(id=id).first()
    g = grade_info.query.filter(grade_info.grade_name!="已毕业").all()
    #class_info.class_name中不包含"届"字的行政班和班级
    c = class_info.query.filter(class_info.class_name.op('NOT LIKE')('%届%')).filter(class_info.attribute=="行政班").all()
    #class_info.class_name中名字以当前用户的学科开头的选考班
    if teacher_.teacher.subject=="信息技术" or teacher_.teacher.subject=="通用技术":
        c1=class_info.query.filter(class_info.class_name.op('LIKE')("技术"+"%")).filter(class_info.attribute=="选考班").all()
    else:
        c1=class_info.query.filter(class_info.class_name.op('LIKE')(teacher_.teacher.subject+"%")).filter(class_info.attribute=="选考班").all()
    c=c+c1
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
            if int(i) not in class_:
                t2=teaching_information(subject=teacher_.teacher.subject,class_id=i,teacher_id=teacher_.teacher.id)
                db.session.add(t2)
        db.session.flush() 
        if id:
            appointed = class_info.query.filter(class_info.class_master==teacher_.teacher.id).first()
            new=class_info.query.filter(class_info.id==id).first()
            if new:
                if appointed:
                    if appointed.id != new.id:
                        appointed.class_master=None
                        teachinfor=teaching_information.query.filter(teaching_information.class_id==appointed.id).filter(teaching_information.teacher_id==teacher_.teacher.id).filter(teaching_information.subject=="master_teacher").first()
                        print(appointed.id,teacher_.teacher.id,teachinfor)
                        if teachinfor:
                            db.session.delete(teachinfor)
                new.class_master = teacher_.teacher.id
                t1=teaching_information(subject="master_teacher",class_id=new.id,teacher_id=teacher_.teacher.id)
                db.session.add(t1)  
        db.session.flush()                
        db.session.commit()        
        return(redirect(url_for("manage.people_management")))
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

@manage.route("/structure/", methods=["POST", "GET"])  # 批量添加数据的方法案例, 设置年级和班级
@login_required 
@permission_required(Permission.admin)
def structure():
    if request.method=="POST":
        grade_id =request.get_json()['grade_id']        
        if grade_id:            
            cla = class_info.query.filter_by(grade_id=grade_id).all()
        else:
            cla = class_info.query.all()
    else:   
        cla=class_info.query.all() 
    grade=grade_info.query.order_by(grade_info.academic_year.desc()).all()  
    return(render_template("manage/structure.html",cla=cla,grade=grade))

@manage.route("/update_class_master/", methods=["POST", "GET"])  # 批量添加数据的方法案例, 设置年级和班级
@login_required 
@permission_required(Permission.admin)
def update_class_master(): 
    if request.method=="POST":
        data=request.get_json()
        messege="不存在的老师："
        m=0
        for i in data:
            c_master=data[i]            
            c_m=user.query.filter(user.realname==c_master).first()
            if c_m:
                cla_=class_info.query.filter(class_info.id==int(i)).first()
                cla_.class_master=c_m.teacher.id
                cla_.teacher.user_info.role_id=role.query.filter(role.role=="master_teacher").first().id
                db.session.flush()
                m+=1         
            else:
                messege+=c_master+" " 
        if m>0:
            messege="成功任命%s位班主任" %m+messege
        db.session.commit()
    return(messege)

@manage.route("/creat_classes/", methods=["POST", "GET"])  # 批量添加数据的方法案例, 设置年级和班级
@login_required 
@permission_required(Permission.admin)
def creat_classes():   
    if request.method=="POST":
        data=request.get_json()
        data=sorted(data,key=lambda d:d['year'],reverse=True)
        print(data)
        g_name=1
        messege=[]
        for i in data:
            g_info=grade_info.query.filter(grade_info.grade_name=="%s年级" %g_name).first()
            if g_info:
                messege.append("%s年级已存在" %g_name)
            else:
                g_info=grade_info(grade_name="%s年级" %g_name,academic_year=i['year'])
                 
                db.session.add(g_info)
                db.session.flush()
            c_name=1
            for j in range(i['num']):
                c_name="%s%s" %(g_name, str(j+1).zfill(2))
                print(c_name)
                if class_info.query.filter(class_info.class_name==c_name).first():
                    messege.append("%s班级已存在" %c_name)
                cla=class_info(class_name=c_name,grade_id=g_info.id,attrbute="行政班")
                db.session.add(cla)
                db.session.flush()
            g_name+=1
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            messege=["数据库写入错误"]     
    return(jsonify( messege))

@manage.route("/teaching_team_leader/", methods=["POST", "GET"])  # 个别添加班级
@login_required 
@permission_required(Permission.admin)
def teaching_team_leader():
    if request.method=="POST":
        id=request.form.get("id")
        status=request.form.get("status")
        ttl=user.query.filter(user.id==id).first()        
        if status=="true":            
            ttl.role_id=role.query.filter(role.role=="教研组长").first().id
        else:
            print(id,status)
            ttl.role_id=role.query.filter(role.role=="teacher").first().id
        db.session.flush()
        db.session.commit()
        return("设置成功")

@manage.route("/create_class/", methods=["POST", "GET"])  # 个别添加班级
@login_required 
@permission_required(Permission.admin)
def creat_class():
    if request.method=="POST":
        name=request.form.get("name")
        year=request.form.get("year")
        grade=grade_info.query.filter(grade_info.academic_year==year).first()
        messege=[]
        if grade:
            if class_info.query.filter(class_info.class_name==name).first():
                messege.append("%s班已存在" %name)
            else:
                cla=class_info(class_name=name,grade_id=grade.id,attribute="选考班")
                db.session.add(cla)
                db.session.flush()
                messege.append("成功添加%s班" %name)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            messege="数据库写入失败"
    return(jsonify(messege)) 

@manage.route("/representative/<arg>")
def rep(arg):
    s=arg.split('-')
    rep=representative.query.filter(representative.teacher_id==s[0],representative.student_id==s[1]).first()
    if not rep:
        if representative.query.filter(representative.student_id==s[1]).first():
            flash("该学生已担任课代表")
        else:
            stu=representative(teacher_id=s[0],student_id=s[1],subject=current_user.teacher.subject)
            db.session.add(stu)
            db.session.flush()
            stu.student.user_infor.role_id=2   
    else:
        db.session.delete(rep)
        rep.student.user_infor.role_id=4
    try:
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback
    return(redirect( url_for("manage.student_overview",id=s[1])))

@manage.route("/graduate/", methods=["POST", "GET"])  # 升班毕业
@login_required
@permission_required(Permission.admin)
def graduate():
    db.session.rollback()
    #从数据库中检索出所有的行政班 
    classes = class_info.query.filter(class_info.attribute=="行政班").order_by(class_info.class_name.desc()).all()
    #从数据库中检索出所有的年级,从大到小排序
    grades = grade_info.query.order_by(grade_info.grade_name.desc()).all()
    print(grades)
    for i in grades:
        if i.academic_year==datetime.datetime.now().year:
            i.grade_name="已毕业"
        else:
            i.grade_name="%s年级" %str(4-(i.academic_year-datetime.datetime.now().year))
        db.session.flush()
    for i in classes:
        if i.grade.academic_year==datetime.datetime.now().year :    
            i.class_name=str(i.grade.academic_year) + "届" + i.class_name
            i.attrbute="毕业班"
        else:
            i.class_name="%s%s" %(i.grade.grade_name[0],i.class_name[1:])
        db.session.flush()
    db.session.commit()
    return(jsonify("毕业设置成功"))


