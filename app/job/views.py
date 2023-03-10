import statistics
from io import BytesIO
from flask_paginate import Pagination, get_page_parameter
from pandas import DataFrame
from .import job_manage
from flask import render_template, redirect, flash, request,jsonify
from ..models import job, job_detail,job_student,job_class, representative,student,class_info,class_student, teaching_information,user,teacher,Permission,grade_info
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
import shutil
import ast
from pyecharts.charts import Bar,Liquid,Grid
from pyecharts import options as opts
from collections import defaultdict
from pyecharts.globals import SymbolType
from pyecharts.commons.utils import JsCode


@job_manage.route("/",methods=["POST","GET"]) # 作业管理主页教师页面为作业情况，学生页面为学生个人信息
@login_required 
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
    count={}
    count1={}
    g=[]
    if  current_user.role.has_permission(Permission.job_grade):
        jobs = job.query.filter(job.subject==current_user.teacher.subject).order_by(job.publish_time.desc()).slice(start,end)
        g=grade_info.query.filter(grade_info.academic_year>=datetime.datetime.now().year).order_by(grade_info.academic_year.desc()).all()       
    elif current_user.role.has_permission(Permission.job_publish):        
        jobs=job.query.join(job_class)\
            .join(class_info).join(teaching_information)\
            .filter(teaching_information.teacher_id==current_user.teacher.id,job.subject==current_user.teacher.subject)\
                .order_by(job.publish_time.desc()).slice(start,end)  
    elif  current_user.role.has_permission(Permission.admin):       
        jobs=job.query.all().order_by(job.publish_time.desc()).slice(start,end)
    class__=current_user.teacher.teaching_information.order_by(teaching_information.class_id.asc())   
    
    dic={}
    pagination = Pagination(page=page, total=len(job.query.all()), bs_version=4, search=search, record_name='job')
    for i in jobs:            
        a=os.path.join(os.getcwd(),"app","static","answer",str(i.id))
        b=os.path.join(os.getcwd(),"app","static","job_readed",str(i.id))
        count[i.id]=len(os.listdir(a))
        count1[i.id]=len(os.listdir(b))
    return(render_template("job/mainpage.html", p=p,dic=dic,jobs=jobs,count=count,count1=count1,Permission=Permission,subjects=["语文","数学","外语","政治","历史","地理","物理","化学","生物","通用技术","信息技术"],pagination=pagination))

@job_manage.route("/stu/<id>",methods=["POST","GET"]) # 学生个人作业情况
def stu_job(id):
    jobs=job_detail.query.filter(job_detail.student==id).all()
    return(render_template("job/stu_job.html",jobs=jobs))

@job_manage.route("/assign_job/<id>",methods=["POST","GET"])
@login_required 
@permission_required(Permission.job_publish)
def assign_job(id):
    if request.method=="GET":
        classes =current_user.teacher.teaching_information.order_by(teaching_information.class_id.asc()).all()
        class_={}
        g1={}
        for i in classes:
            if job_class.query.filter(job_class.class_id==i.class_id).filter(job_class.job_id==id).first():
                class_["%s-%s"%(i.class_id,i.class_info.class_name)]=True
            else:
                class_["%s-%s"%(i.class_id,i.class_info.class_name)]=False
        if current_user.role.has_permission(Permission.job_grade):
            g =grade_info.query.filter(grade_info.academic_year>datetime.datetime.now().year)
        for i in g:
            g1[i.id]=i.grade_name
        
        return jsonify(class_,g1)
    if request.method=="POST":
        data=json.loads(request.form.get("list"))
        n=0
        for i in data:
            j_c=job_class.query.filter(job_class.class_id==i).filter(job_class.job_id==id).first()
            if not j_c:
                n+=1
                j_c=job_class(class_id=i,job_id=id)
                db.session.add(j_c)
                db.session.flush()
                students=class_info.query.filter(class_info.id==i).first().students
                for j in students:
                        j_stu=job_student(job_id=id,student=j.number)
                        db.session.add(j_stu)
                        db.session.flush()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return("添加了%s个班级的作业" %n) 
    
@job_manage.route("/question_statistics/",methods=["POST","GET"]) # 班级小题统计
@login_required 
@permission_required(Permission.job_publish)
def question_statistics():
    if request.method=='POST':
        class_id =request.form.get("class_id")        
        job_id=request.form.get("job_id")
        
        if class_id == '0' and current_user.role.has_permission(Permission.job_grade):
            job_details=job_detail.query.filter(job_detail.job_id==job_id).all()
        elif class_id=="0":
            job_details = job_detail.query.join(student)\
            .join(class_student)\
            .join(class_info)\
            .join(teaching_information)\
            .filter(job_detail.job_id == job_id, teaching_information.teacher_id == current_user.teacher.id).all()
        else:
            job_details = job_detail.query.join(student)\
            .join(class_student)\
            .join(class_info)\
            .filter(job_detail.job_id == job_id, class_info.id == class_id).all()
        job_=job.query.filter(job.id==job_id).first()
        tags =json.loads(job_.context)
        answers=job_.select_answer[:-1].split(" ")        
        groups = defaultdict(list)
        for detail in job_details:
            groups[detail.serial_No].append(detail)
        groups =dict(sorted(groups.items()))
        # 绘制每道题的选择情况
        bar_charts = []
        for serial_No, details in groups.items():
            choices = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
            for detail in details:
                choices[detail.answer[0]] += 1
            x_data = ['A', 'B', 'C', 'D']
            item_colors = []            
            correct_item =  answers[serial_No-1]
            for i in x_data:
                if i == correct_item:
                    item_colors.append('#32cd32')
                else:
                    item_colors.append('#ff4500')
            b_num = choices[correct_item]
            total_num = sum(choices.values())
            b_percent = round(b_num / total_num*100, 1)
            bar_chart = (
                Bar(init_opts=opts.InitOpts(width='150px', height='300px')) #设置图表大小
                .add_xaxis(x_data)
                .add_yaxis("", [choices["A"],choices["B"],choices["C"],choices["D"]],color='#004080',
                           markpoint_opts=opts.MarkPointOpts(
                            data=[
                
                                opts.MarkPointItem(value=f'{b_percent}%',coord=[correct_item,choices[correct_item]], name="正确率",itemstyle_opts=opts.ItemStyleOpts(color="#55ff37" if b_percent > 70 else "#dbff5e" if b_percent>60 else "#feaf2c" if  b_percent>50 else "red" ))
                            ]
                        ),)
                .set_global_opts(title_opts=opts.TitleOpts(title=f'第 {serial_No}题：',subtitle=f'{tags[serial_No-1]}'))     
            )
            bar_charts.append(bar_chart) 
        # 将图表转换为HTML字符串并返回给前端
        bar_html_list = [chart.render_embed() for chart in bar_charts]
        return json.dumps(bar_html_list)

        
    

def job_sub(submist_list):
    pass

@job_manage.route("/job_info/<job_id>",methods=["POST","GET"])  # 作业详情
@login_required 
@permission_required(Permission.job_publish)
def job_info(job_id):
    job_=job.query.filter(job.id==job_id).first() 
    cla = job_class.query.filter(job_class.job_id==job_id).all()
    if not job_ and job_.subject!=current_user.teacher.subject:
        return("该作业不存在或你没有查看该作业的权限")  
    if (current_user.role.has_permission(Permission.job_grade)):
        classes_=job_class.query.filter(job_class.job_id==job_id).all()
    else:
        classes_=db.session.query(job_class)\
    .join(teaching_information, teaching_information.class_id == job_class.class_id)\
    .join(teacher, teacher.id == teaching_information.teacher_id)\
    .filter(teacher.id == current_user.teacher.id, job_class.job_id == job_id)\
    .all()
    if not classes_:
        return("该作业没有布置给你的任教班级")
    if request.method=="POST":
        class_id=request.form.get("class_id")
        class_=class_info.query.filter(class_info.id== class_id).first()       
    else:
        class_=class_info.query.filter(class_info.id==classes_[0].class_id).first()
    if class_:
        jobs = db.session.query(job_student).join(student).join(class_student).filter(class_student.class_id == class_.id,job_student.job_id==job_id).all()
    else:
        jobs=[]
    sum_=job_.select*job_.s_m
    marks = [job.mark for job in jobs if job.mark!=None]
    f = len([job.mark for job in jobs if job.mark==None])
    class_names = [data.class_info.class_name for data in cla]
    max_scores = [data.max for data in cla]
    min_scores = [data.min for data in cla]
    avg_scores = [data.average for data in cla]
    bar = (
        Bar()
        .add_xaxis(class_names)
        .add_yaxis("最高分", max_scores)
        .add_yaxis("最低分", min_scores)
        .add_yaxis("平均分", avg_scores)
        .set_series_opts(
            label_opts=opts.LabelOpts(is_show=False),
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="《{}》各班级分数对比".format(job_.job_name)),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
            yaxis_opts=opts.AxisOpts(min_=0, max_=sum_),
        )
    )
    js={}
    for i in jobs:
        jt=job_detail.query.filter(job_detail.job_id==i.job_id, job_detail.student==i.student)
        data=[]
        for j in range(job_.select):
            
            data.append(jt.filter(job_detail.serial_No==j+1).first())
            
        js[i.id]=data    
    charts=bar.render_embed()
    dict={'id':job_id,"name":job_.job_name,"select":int(job_.select),"publish_time":job_.publish_time,"deadline":job_.deadline,"sum":sum_,"n_sub":f}
    return(render_template("job/job_info.html",dict=dict,jobs=jobs,classes_=classes_,class_=class_,js=js,charts=charts))


@job_manage.route("/show_paper/<url>",methods=["POST","GET"])#
@login_required 
@permission_required(Permission.job_publish)
def show_paper(url):
    url="./paper/excercise/"+url
    return(render_template("job/show_paper.html",url=url))

@job_manage.route("/genarate_paper",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def genarate_paper():
    if current_user.role.has_permission(Permission.job_publish):
        class__=current_user.teacher.teaching_information.order_by(teaching_information.class_id.asc())
        class_=[]
        for i in class__:
            if i.class_info not in class_:
                class_.append(i.class_info)
    elif current_user.role.role=="representative":
        class_.append(current_user.student.class_info)
    if current_user.role.has_permission(Permission.job_grade):
        pass
    g=grade_info.query.all()
    if request.method == "POST":
        flag=request.form.get("flag")
        if flag=="1":
            title=request.form.get("title")
            if job.query.filter(job.job_name==title).first():
                return("已存在该作业")
            number = request.form.get("number")
            select = request.form.get("select")
            subtopic =request.form.getlist("subtopic[]") # ajax获取列表，要在字典key后加上[]
            c_mark=request.form.get("c_mark")
            teacher = current_user.realname
            publish_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
            publisher=current_user.id
            deadline=request.form.get("time")
           #deadline =datetime.datetime.strptime(deadline,"/%Y/%m/%d")             
            g=request.form.getlist("grade[]")            
            if current_user.role.has_permission(Permission.job_publish): 
                teacher = current_user.teacher.id
                subject=current_user.teacher.subject
            r=creat_paper.paper(subject,current_user.realname,2000,title,int(select),subtopic)
            url = "/static/paper/excercise/"+str(teacher)+"-"+str(time.time())+".png"                
            r[-1].save(os.getcwd()+"/app"+url)            
            s_answer=request.form.getlist("answers")
            tags=request.form.getlist("tags[]")
            job_submit = job(job_name=title,publish_time=publish_time,publisher=publisher,deadline=deadline,subject=subject,select_answer=s_answer,context=json.dumps(tags),paper_url=url,s_m=int(number),complete=c_mark,line=json.dumps(r[0]),select=int(select))
            db.session.add(job_submit)
            db.session.flush()
            path=os.getcwd()+"/app/static/answer/"+str(job_submit.id)
            path1=os.getcwd()+"/app/static/job_readed/"+str(job_submit.id)
            if not os.path.exists(path):
                os.makedirs(path)
            if not os.path.exists(path1):    
                os.makedirs(path1)
            print(g)
            if g:
                class_list=db.session.query(class_info).join(grade_info).filter(grade_info.id.in_(g)).filter(class_info.attribute=="行政班").all()
                
            else:          
                class_list=db.session.query(class_info).filter(class_info.id.in_(request.form.getlist("classlist[]"))).all()
            
            print(class_list)
            if class_list:  # 作业布置                
                data={}
                data["status"]=0
                for i in class_list:                    
                    check_job=job_class.query.join(job,job_class.job).filter(job.job_name==title,job_class.class_id==i.id,job.subject==current_user.teacher.subject).first()  #避免重复布置相同作业
                    if check_job:
                        data["status"]+=1
                        data["%s" %data["status"]]="%s班已经有名为《%s》的作业！" %(check_job.class_info.class_name,title)
                        db.session.rollback()                       
                    else:
                        job_publish = job_class(class_id=i.id,job_id=job_submit.id)
                        db.session.add(job_publish)
                        db.session.flush()
                        for j in i.students:
                            j_stu=job_student(job_id=job_submit.id,student=j.number)
                            db.session.add(j_stu)
                            db.session.flush()
                db.session.commit()
                if data['status']==0:
                    data["url"]=url
                return(data)
            else:
                db.session.rollback()
                return("没有设置班级")            
    return(render_template("job/genarate_paper.html",g=g,class_=class_,Permission=Permission))

@job_manage.route("/del/",methods=["POST"])  #
@login_required 
@permission_required(Permission.job_publish)
def del_job():
    url=request.form.get("url")
    try:
        job_=job.query.filter(job.paper_url==url).first()       
        db.session.delete(job_)
        db.session.flush()
        db.session.commit()
        return("已删除该作业")
    except Exception:
        db.session.rollback()
        return("删除作业失败，请在作业主界面删除")

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
                file.save(os.path.join(os.getcwd(),url, filename))
                n+=1
            except Exception:
                pass        
        count=len(os.listdir(url))
        return(jsonify([n,count]))
       
@job_manage.route("/judge/<id>",methods=["POST","GET"]) #
@login_required 
@permission_required(Permission.job_publish)
def job_judge(id):
    job_=job.query.filter(job.id==id).first()
    n=0
    if len(job_.line)>2:
        judge.line=list(map(int,job_.line[1:-1].split(",")))
    answers=job_.select_answer[:-1].split(" ")
    select=job_.select 
    img=judge.open(os.getcwd()+"/app"+job_.paper_url)
    split=judge.paper_split(img,select,judge.line)
    root=os.getcwd()+"/app/static/answer/"+str(id)
    tags = json.loads(job_.context)
    for dirpath, dirnames, filenames in os.walk(root): #遍历答题卷文件夹阅卷
        for filepath in filenames:
            ep=judge.open2(os.path.join(dirpath, filepath))
            ep=judge.paper_ajust(img,ep) 
                     
            #if judge.qr(img)==judge.qr(ep):
            
            split=judge.paper_split(ep,select,judge.line)
            number=judge.number_pos(split[0]) 
               
            j_stu=job_student.query.filter(job_student.job_id==int(id),job_student.student==number).first()
            if j_stu: #判断该生是否有作业任务，若无，不作阅卷处理
                s=judge.check_select(split[1],select) 
                print(number,s)             
                se=0           
                for key in s:
                    if key>len(answers):
                        continue
                    if job_detail.query.filter(job_detail.student==number,job_detail.job_id==int(id),job_detail.serial_No==key).first():
                        
                        continue
                    else:                        
                        mark=0
                        if s[key]==answers[key-1]:                            
                            mark=2
                            se+=2
                        
                        jt=job_detail(job_id=int(id),student=number,serial_No=key,answer=s[key],mark=mark,tag=tags[key-1])
                    db.session.add(jt)
                    db.session.flush()
                if j_stu.select_mark==None:
                    j_stu.select_mark=0
                    j_stu.mark=0
                    j_stu.complete_mark=0
                j_stu.select_mark=se  #以下为学生作业统计
                j_stu.mark+=se+j_stu.complete_mark
                n+=1
                shutil.move(os.path.join(dirpath, filepath), os.path.join(os.getcwd(),"app","static","job_readed",str(id),"%s.jpg"%number))
            else:
                print(number+"无该作业")
    j_cla=job_class.query.filter(job_class.job_id==int(id)).all()  #阅卷完成后统计作业情况，查询被布置了此作业的所有班级
    for i in j_cla: #遍历所有班级，依次统计
        class_=class_info.query.filter(class_info.id==i.class_id).first()
        j_stu = db.session.query(job_student).filter(job_student.job_id==int(id),job_student.student.in_([s.number for s in class_.students])).all()
        if j_stu:
            marks = [j.mark for j in j_stu if j.mark is not None]
            i.submit_number = len(marks)
            if len(marks)!=0:
                i.average = sum(marks) / len(marks)
                i.max = max(marks)
                i.min = min(marks)
        db.session.flush()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return(jsonify(n))