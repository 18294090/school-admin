import statistics
from io import BytesIO
from flask_paginate import Pagination, get_page_parameter
from pandas import DataFrame
from .import job_manage
from flask import render_template, redirect, flash, request,jsonify
from ..models import job, representative,student,class_info, teaching_information,user,teacher,Permission,job,job_class
from .. import db
from .forms import publish
from flask_login import current_user,login_required
from sqlalchemy import func
import time
import datetime
import os
from .paper import creat_paper,judge
from ..decorators import permission_required
import json
from werkzeug.utils import secure_filename


@job_manage.route("/",methods=["POST","GET"]) # 作业管理主页教师页面为作业情况，学生页面为学生个人信息
def job_mg():
    if current_user.role.role=="student":
        return (redirect("/manage/student/%s" %current_user.student.id))
   
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    p = publish()
    search = False  # 分页切片，flask_paginate模块实现
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page-1)*10
    end =page*10
    class_=[]
    count={}
    if current_user.role.role=="teacher":
        jobs=job.query.filter(job.teacher_id==current_user.teacher.id).order_by(job.publish_time.desc()).slice(start,end)
        class__=current_user.teacher.teaching_information.order_by(teaching_information.class_id.asc())
        
        for i in jobs:
            a=os.path.join(os.getcwd()+"/app/static/answer/"+str(i.id))
            count[i.id]=len(os.listdir(a))
        for i in class__:
            if i.class_info not in class_:
                class_.append(i.class_info)
    elif current_user.role.role=="representative":
        re=current_user.student.representative.all()
        id=[]
        class_=[]
        for i in re:
            id.append(i.teacher_id)
        jobs = job.query.filter(job.class_id==current_user.student.class_info.id).filter(job.teacher_id.in_(id)).order_by(job.publish_time.desc()).slice(start,end)
        class_.append(current_user.student.class_info)
        for i in jobs:
            a=os.path.join(os.getcwd()+"/app/static/answer/"+str(i.id))
            count[i.id]=len(os.listdir(a))
    elif current_user.role.role == "admin":
        jobs = job.query.slice(start,end)        
        for i in jobs:
            a=os.path.join(os.getcwd()+"/app/static/answer/"+str(i.id))
            count[i.id]=len(os.listdir(a))
        class_=[]   
    dic={}
    pagination = Pagination(page=page, total=len(job.query.all()), bs_version=4, search=search, record_name='job')
   
    return(render_template("job/mainpage.html", p=p,dic=dic,class_=class_,jobs=jobs,count=count,Permission=Permission,subjects=["语文","数学","外语","政治","历史","地理","物理","化学","生物","通用技术","信息技术"],pagination=pagination))



@job_manage.route("/stu/<id>",methods=["POST","GET"]) # 学生个人作业情况
def stu_job(id):
    jobs=job_submission.query.filter(job_submission.student==id).all()
    return(render_template("job/stu_job.html",jobs=jobs))

@job_manage.route("/job_assessment/<job_id>",methods=["POST","GET"]) # 学生作业评价
def job_assessment(job_id):
    job_=job.query.filter(job.id==job_id).first()
    if job_.teacher_id!=current_user.teacher.id:
        return("你不是该作业的责任教师，无法评价")
    jobs=job.query.filter(job.id==job_id).first().job_submission
    return(render_template("job/job_assessment.html",jobs=jobs,job_submission=job_submission))

@job_manage.route("/assess/<id>",methods=["POST","GET"]) # 学生作业评分
def mark(id):
    if request.method == 'POST':
        data = request.get_json()
        for key in data:
            if data[key]!="选择分数等第":
                job_sub=job_submission.query.filter(job_submission.id==key).first()                
                job_sub.mark=int(data[key][0])
                job_sub.job_assessment=data[key][1]           
                db.session.flush()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return("数据库写入错误")
    return jsonify("成功评价%s人" %len(data))

@job_manage.route("/del/",methods=["POST","GET"]) # 删除作业
def job_submit_del():
    if request.method=='POST':
        data =request.get_json()
        
        id=data["del"]
        print(id)
        j=job.query.filter(job.id==id).first()
        sub=job_submission.query.filter(job_submission.job_id==j.id).all()

        db.session.delete(j)
        db.session.flush()
    try:
        db.session.commit()
        return jsonify("删除成功")
    except Exception:
        db.session.rollback()
        return("数据库写入错误")

@job_manage.route("/judge/",methods=["POST","GET"]) # 设定批改状态
def set_judge():
    if request.method=='POST':
        data =request.get_json()
        
        id=data["judge"]
        j=job.query.filter(job.id==id).first()
        j.judged=True
        db.session.flush()
    try:
        db.session.commit()
        return jsonify("设置成功")
    except Exception:
        db.session.rollback()
        return("数据库写入错误")


def job_sub(submist_list):
    pass

@job_manage.route("/job_info/<job_id>",methods=["POST","GET"])  # 班级单个作业详情
def job_info(job_id):
    job_=job.query.filter(job.id==job_id).first()
    if not job_:
        return("该作业不存在")
    if (current_user.teacher and job_.teacher_id!=current_user.teacher.id) or(current_user.student and job_.class_id!=current_user.student.class_info.id):
        return("没有查看该作业的权限")
    search = False  # 分页切片，flask_paginate模块实现
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page-1)*10
    end =page*10
    jobs=job_submission.query.filter(job_submission.job_id==job_id).order_by(job_submission.mark.asc()).slice(start,end)
    pagination = Pagination(page=page, total=len(job_submission.query.filter(job_submission.job_id==job_id).all()), bs_version=4, search=search, record_name='jobs')
    n = len(job_submission.query.filter(job_submission.job_id==job_id).filter(job_submission.submit_time==None).all())
    class_name = job.query.filter(job.id==job_id).first().class_info.class_name
    aver =job_submission.query.filter(job_submission.job_id==job_id).with_entities(func.avg(job_submission.mark)).scalar()
    return(render_template("job/job_info.html",job_submission=jobs,n=n,class_name=class_name,aver=aver,pagination=pagination))

@job_manage.route("/teacher_statistics/",methods=["POST","GET"]) # 教师作业统计                                                                    
def teacher_statistics():
    if not current_user.role.has_permission(Permission.teacher_info):
        return("没有权限")
    t = teacher.query.all()
    statistics =DataFrame(columns=["姓名","作业数量","提交率","批改数","平均分","学科"])
    for i in t:
        jobs = job.query.filter(job.teacher_id==i.id)
        job_count =jobs.with_entities(func.count(job.id)).scalar()
        assess_rate =jobs.filter(job.judged == 1).with_entities(func.count(job.id)).scalar()
        j_s = job_submission.query.filter(job_submission.teacher_id==i.id)
        if j_s.with_entities(func.count(job_submission.id)).scalar():
            sub_rate = j_s.filter(job_submission.submit_time != None).with_entities(func.count(job_submission.id)).scalar()/j_s.with_entities(func.count(job_submission.id)).scalar()
            print(jobs.filter(job.judged == True).all())
            aver = j_s.with_entities(func.avg(job_submission.mark)).scalar()
        else:
            sub_rate=0
            aver =0            
        statistics.loc[i.id]=[i.user_info.realname,job_count,round(sub_rate*100,2),assess_rate,aver,i.subject]
    return(render_template("job/teacher_statistics.html",teacher=t,statistics=statistics))

def class_statistics_(class_,subject):
    pass

@job_manage.route("/class_statistics/<subject>/<class_id>",methods=["POST","GET"])
def class_statistics(subject,class_id):
    if not current_user.role.has_permission(Permission.job_info) or current_user.role.role=="teacher" and current_user.teacher.teaching_information.filter(teaching_information.class_id==class_id).all()==None or current_user.role.role=="representative" and (current_user.student.representative.first().subject!=subject or current_user.student.class_id !=int(class_id)):  # 权限检查 
        return("没有权限")
    statistics =DataFrame(columns=["姓名","学科","未提交","平均分","作业数量"])
    stu=student.query.filter(student.class_id==class_id).all()
    class_ = class_info.query.filter(class_info.id==class_id).first()
    for i in stu:
        if subject=="全科":
            n_sub = job_submission.query.filter(job_submission.student==i.id).filter(job_submission.submit_time==None).count()
            aver = job_submission.query.filter(job_submission.student==i.id).filter(job_submission.submit_time!=None).with_entities(func.avg(job_submission.mark)).scalar()
            job_count = job.query.filter(job.class_id==class_id).count()
        else:
            teacher_id =teaching_information.query.filter(teaching_information.class_id==class_id).filter(teaching_information.subject==subject).first()
            if teacher_id:
                teacher_id =teacher_id.teacher.id
                
            else:
                return("该班级没有该学科的教师")
            n_sub = job_submission.query.filter(job_submission.teacher_id==teacher_id).filter(job_submission.student==i.id).filter(job_submission.submit_time==None).count()
            aver = job_submission.query.filter(job_submission.student==i.id).filter(job_submission.teacher_id==teacher_id).filter(job_submission.submit_time!=None).with_entities(func.avg(job_submission.mark)).scalar()
            job_count = job.query.filter(job.class_id==class_id).filter(job.teacher_id==teacher_id).count()
            print(teacher_id,n_sub)
        if not aver:
            aver=0
        statistics.loc[i.id]=[i.user_infor.realname,subject,n_sub,round(aver,2),job_count]
    statistics.sort_values(by="平均分",ascending=False,inplace=True)    
    search = False
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page-1)*10
    end =page*10
    statistics_=statistics[start:end]
    pagination = Pagination(page=page, total=len(statistics), bs_version=4, search=search, record_name='statistics')
    return(render_template("job/class_teacher_statistics.html",subject=subject,class_=class_,statistics=statistics_,pagination=pagination))

@job_manage.route("/current_job/",methods=["POST","GET"])  # 班级当前作业列表
def current_job():
    jobs=job.query.filter(job.class_id==current_user.student.class_id,job.deadline>datetime.datetime.now()).all()
    j=[]
    for i in jobs:
        sub=job_submission.query.filter(job_submission.job_id==i.id,job_submission.student==current_user.student.id).first()
        if sub.submit_time ==None:
            f="未提交"
        else:
            f="已提交"
        j.append({"job_name":i.job_name,"deadline":i.deadline,"subject":i.subject,"status":f,"context":i.context})
    return(render_template("job/current_job.html",jobs=j))

@job_manage.route("/show_paper/<url>",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def show_paper(url):
    url="./paper/excercise/"+url
    return(render_template("job/show_paper.html",url=url))

@job_manage.route("/genarate_paper",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def genarate_paper():
    if current_user.role.role=="teacher":
        class__=current_user.teacher.teaching_information.order_by(teaching_information.class_id.asc())
        class_=[]
        for i in class__:
            if i.class_info not in class_:
                class_.append(i.class_info)
    elif current_user.role.role=="representative":
        class_.append(current_user.student.class_info)
    if request.method == "POST":
        flag=request.form.get("flag")
        if flag=="1":
            title=request.form.get("title")
            number = request.form.get("number")
            select = request.form.get("select")
            subtopic =request.form.getlist("subtopic[]") # ajax获取列表，要在字典key后加上[]
            c_mark=request.form.get("c_mark")
            teacher = current_user.realname
            publish_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            publisher=current_user.id
            deadline=request.form.get("time")
           #deadline =datetime.datetime.strptime(deadline,"/%Y/%m/%d")
            context =request.form.get("context")           
            if current_user.role.role=="teacher": 
                teacher = current_user.teacher.id
                subject=current_user.teacher.subject
            else:
                teacher = current_user.student.representative.first().teacher_id
                subject =  current_user.student.representative.first().subject
            r=creat_paper.paper(subject,current_user.realname,2000,title,int(select),subtopic)
            url = "/static/paper/excercise/"+str(teacher)+"-"+str(time.time())+".png"                
            r[-1].save(os.getcwd()+"/app"+url)
            job_submit = job(job_name=title,publish_time=publish_time,publisher=publisher,teacher_id=teacher,deadline=deadline,subject=subject,context=context,paper_url=url,s_m=int(number),complete=c_mark,line=json.dumps(r[0]),select=int(select))
            db.session.add(job_submit)
            db.session.flush()
            path=os.getcwd()+"/app/static/answer/"+str(job_submit.id)
            if not os.path.exists(path):
                os.makedirs(path)
            class_list=request.form.getlist("classlist[]")
            if class_list:  # 作业布置                
                data={}
                data["status"]=0
                for i in class_list:                    
                    check_job=job_class.query.join(job,job_class.job).filter(job.job_name==title,job_class.class_id==i,job.teacher_id==teacher).first()  #避免重复布置相同作业
                    if check_job:
                        data["status"]+=1
                        data["%s" %data["status"]]="%s班已经有名为《%s》的作业！" %(check_job.class_info.class_name,title)
                        db.session.rollback()                       
                    else:
                        job_publish = job_class(class_id=i,job_id=job_submit.id)
                        db.session.add(job_publish)
                db.session.flush()
                db.session.commit()
                if data['status']==0:
                    data["url"]=url
                return(data)
            else:
                return("没有设置班级")
        else:
            url=request.form.get("url")
            try:
                job.query.filter(job.paper_url==url).delete()
                db.session.commit()
                return("已删除该作业")
            except Exception:
                db.session.rollback()
                return("删除作业失败，请在作业主界面删除")
    return(render_template("job/genarate_paper.html",class_=class_))

@job_manage.route("/upload/<id>",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def upload_paper(id):
    if request.method == 'POST':
        url=os.getcwd()+"/app/static/answer/"+str(id)
        files = request.files.getlist("files")
        n=0
        for file in files:            
            filename=secure_filename(file.filename)
            try:
                file.save(os.path.join(os.getcwd()+"/app/static/answer/"+str(id), filename))
                n+=1
            except Exception:
                pass        
        a=os.getcwd()+"/app/static/answer/"+str(id)
        count=len(os.listdir(a))
        return(jsonify([n,count]))
       
@job_manage.route("/judge/<id>",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def job_judge(id):
    job_=job.query.filter(job.id==id).first()
    n=0
    judge.line=job_.line
    select=job.select 
    print(judge.line)
    img=judge.open(os.getcwd()+"/app"+job_.paper_url) 
    root=os.getcwd()+"/app/static/answer/"+str(id)
    for dirpath, dirnames, filenames in os.walk(root): 
        for filepath in filenames:
            ep=judge.open2(img,os.path.join(dirpath, filepath))
            if judge.qr(img)==judge.qr(ep):
                dst=judge.paper_ajust(img,ep)
                split=judge.paper_split(dst,select,judge.line)
                number=judge.number_pos(split[0])
                n+=1
    return(jsonify(n))
        