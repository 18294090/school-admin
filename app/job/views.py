from .import job_manage
from flask import render_template, redirect, flash, request,jsonify
from ..models import job_submission,job, representative,student,class_info
from .. import db
from .forms import publish
from flask_login import current_user
from sqlalchemy import func
import time
import datetime

@job_manage.route("/",methods=["POST","GET"])
def job_mg():
    if request.method == "POST":
        class_list=request.form.getlist("cla")
        submit_list =request.form.getlist("stu")
        if class_list:
            for i in class_list:
                job_name=request.form.get("job_name")
                publish_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                publisher=current_user.id
                deadline=request.form.get("time")
                if current_user.role.role=="teacher": 
                    teacher = current_user.teacher.id
                    subject=current_user.teacher.subject
                else:
                    teacher = current_user.student.representative.first().teacher_id
                    subject =  current_user.student.representative.first().subject
                check_job=job.query.filter(job.job_name==job_name,job.class_id==i,job.teacher_id==teacher).first()  #避免重复布置相同作业
                if check_job:
                    flash("%s班已经有名为《%s》的作业！" %(check_job.class_info.class_name,job_name))
                else:
                    job_submit = job(job_name=job_name,publish_time=publish_time,publisher=publisher,teacher_id=teacher,deadline=deadline,subject=subject, class_id=i)
                    db.session.add(job_submit)
                    db.session.flush()
                    for j in class_info.query.filter(class_info.id==i).first().student:
                        submission=job_submission(job_id=job_submit.id,student=j.id)
                        db.session.add(submission)
                        db.session.flush()
        if submit_list:
            for i in submit_list:
                job_id,student=i.split("-")
                job_sub=job.query.filter(job.id==job_id).first()
                if job_sub.deadline < datetime.datetime.now():
                    flash("已过截止时间，不能提交")
                    break
                verify_sub=job_submission.query.filter(job_submission.job_id==job_id,job_submission.student==student).first()
                verify_sub.submit_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                db.session.flush()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    p = publish()
    if current_user.role.role=="teacher":
        jobs=current_user.teacher.jobs
    elif current_user.role.role=="representative":
        re=current_user.student.representative.all()
        id=[]
        for i in re:
            id.append(i.teacher_id)
        jobs =job.query.filter(job.class_id==current_user.student.class_info.id).filter(job.teacher_id.in_(id)).order_by(job.publish_time.desc()).all()
    else:
        jobs=[]
    dic={}
    
    for i in jobs:
        dic[i.id]=job_submission.query.filter(job_submission.job_id==i.id).with_entities(func.avg(job_submission.mark)).scalar()  # 从数据库统计班级每个作业的平均分
        print(dic[i.id])
    return(render_template("job/mainpage.html", p=p,job_submission=job_submission,dic=dic,jobs=jobs,job=job))

@job_manage.route("/job_assessment/<job_id>",methods=["POST","GET"])
def job_assessment(job_id):
    jobs=job.query.filter(job.id==job_id).first().job_submission
    return(render_template("job/job_assessment.html",jobs=jobs,job_submission=job_submission))

@job_manage.route("/assess/<id>",methods=["POST","GET"])
def mark(id):
    if request.method == 'POST':
        data = request.get_json()
        for key in data:
            if data[key]!="选择分数等第":
                job_sub=job_submission.query.filter(job_submission.id==key).first()                
                job_sub.mark=int(data[key])
                db.session.flush()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return("数据库写入错误")
    return jsonify("成功评价%s人" %len(data))

@job_manage.route("/del/",methods=["POST","GET"])
def job_submit_del():
    if request.method=='POST':
        data =request.get_json()
        print(data)
        id=data["del"]
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
    
