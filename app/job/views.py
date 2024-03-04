from flask_paginate import Pagination, get_page_parameter
import pandas as pd
from .import job_manage
from flask import render_template, redirect, flash, request,jsonify,make_response,send_from_directory,abort
from ..models import job, job_detail,job_student,job_class,difficult, student,class_info,class_student, teaching_information,user,teacher,Permission,grade_info,abnormal_job
from .. import db
from .forms import publish
from flask_login import current_user,login_required
from sqlalchemy import func ,or_,cast
import time
import datetime
import os
from .paper import creat_paper,judge
from ..decorators import permission_required
import json
from werkzeug.utils import secure_filename
import shutil
from pyecharts.charts import Bar,Pie,HeatMap,Line
from pyecharts import options as opts
from collections import defaultdict
from pyecharts.globals import SymbolType
from pyecharts.commons.utils import JsCode
import cv2
import base64
import mammoth
import itertools
import random
import numpy as np
from PIL import Image


@job_manage.route("/",methods=["POST","GET"]) # 作业管理主页教师页面为作业情况，学生页面为学生个人信息
@login_required 
def job_mg():
    if current_user.role.role=="student": # type: ignore
        return (redirect("/manage/student/%s" %current_user.student.id)) # type: ignore
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
    if  current_user.role.has_permission(Permission.admin):             
        jobs=job.query.order_by(job.publish_time.desc()).slice(start,end)               
    elif current_user.role.has_permission(Permission.job_grade):
        jobs = job.query.filter(job.subject==current_user.teacher.subject).order_by(job.publish_time.desc()).slice(start,end)
        g=grade_info.query.filter(grade_info.academic_year>=datetime.datetime.now().year).order_by(grade_info.academic_year.desc()).all()      
    elif  current_user.role.has_permission(Permission.job_publish):
        try:        
            jobs=job.query.join(job_class)\
                    .join(class_info).join(teaching_information)\
                    .filter(job.subject==current_user.teacher.subject)\
                    .filter(or_(job.publisher==current_user.id,teaching_information.teacher_id==current_user.teacher.id))\
                        .order_by(job.publish_time.desc()).slice(start,end)
        except Exception:
            return(render_template("404.html",error="没有任教班级"))
    #class__=current_user.teacher.teaching_information.order_by(teaching_information.class_id.asc())   
    pagination = Pagination(page=page, total=len(job.query.all()), bs_version=4, search=search, record_name='job')
    for i in jobs:            
        a=os.path.join(os.getcwd(),"app","static","job","answer",str(i.id))
        b=os.path.join(os.getcwd(),"app","static","job","job_readed",str(i.id))
        count[i.id]=len(os.listdir(a))
        count1[i.id]=len(os.listdir(b))
    return(render_template("job/mainpage.html", p=p,jobs=jobs,count=count,count1=count1,Permission=Permission,subjects=["语文","数学","外语","政治","历史","地理","物理","化学","生物","通用技术","信息技术"],pagination=pagination))

@job_manage.route("/search_job/<name>",methods=["POST","GET"]) # 作业管理主页教师页面为作业情况，学生页面为学生个人信息
@login_required 
def search_job(name):
    search = False  # 分页切片，flask_paginate模块实现
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page-1)*10
    end =page*10
    if name!="all":
        jobs=job.query.filter(job.job_name.like("%"+name+"%")).order_by(job.publish_time.desc()).slice(start,end)
    else:
        jobs=job.query.order_by(job.publish_time.desc()).slice(start,end)
    count={}
    count1={}
    p = publish()
    pagination = Pagination(page=page, total=len(job.query.all()), bs_version=4, search=search, record_name='job')
    for i in jobs:            
        a=os.path.join(os.getcwd(),"app","static","job","answer",str(i.id))
        b=os.path.join(os.getcwd(),"app","static","job","job_readed",str(i.id))
        count[i.id]=len(os.listdir(a))
        count1[i.id]=len(os.listdir(b))
    return(render_template("job/mainpage.html", p=p,pagination =pagination,jobs=jobs,count=count,count1=count1,Permission=Permission,subjects=["语文","数学","外语","政治","历史","地理","物理","化学","生物","通用技术","信息技术"]))

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
            j_c=job_class.query.filter(job_class.class_id==i[0]).filter(job_class.job_id==id).first()
            if i[1]==True:                
                if not j_c:
                    n+=1
                    j_c=job_class(class_id=int(i[0]),job_id=int(id))
                    db.session.add(j_c)
                    db.session.flush()
                    students=class_info.query.filter(class_info.id==int(i[0])).first().students
                    for j in students:
                            j_stu=job_student(job_id=id,student=j.number)
                            db.session.add(j_stu)
                            db.session.flush()
            else:
                if j_c:
                    db.session.delete(j_c)
                    j_s=job_student.query.join(student).join(class_student).join(class_info).filter(job_student.job_id==id).filter(class_info.id==int(i[0])).filter(job_student.submit_time==None).all()
                    for j in j_s:
                        db.session.delete(j)
                    db.session.flush()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return(jsonify("添加失败"))
        return(jsonify("添加了%s个班级的作业" %n))
    
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
        answers=json.loads(job_.select_answer)
        groups = defaultdict(list)
        for detail in job_details:
            groups[detail.serial_No].append(detail)
        groups =dict(sorted(groups.items()))
        # 绘制每道题的选择情况
        bar_charts = []
        for serial_No, details in groups.items():
            if str(serial_No) in json.loads(job_.select_answer).keys():
                choices = {'A': 0, 'B': 0, 'C': 0, 'D': 0,'AB':0,'AC':0,'AD':0,'BC':0,'BD':0,'CD':0,'ABC':0,'ABD':0,'ACD':0,'BCD':0,'ABCD':0}
                choices_={'A':"",'B':"",'C':"",'D':""}             
                total_num=0
                for detail in details:
                    if detail.answer:
                        #将答案字符串排序
                        detail.answer="".join(sorted(detail.answer))
                        total_num+=1
                        #判断答案是否为choices中的一个键，如果是，该键对应的值加1
                        if detail.answer in choices.keys():
                            choices[detail.answer] += 1
                        if len(detail.answer)>1:
                            for answer in detail.answer:                    
                                choices[answer] += 1
                                #将每个选项的选择人员名单存入choices_字典中
                                choices_[answer]+=" "+detail.stu.name
                                if len(choices_[answer].split())%2==0:
                                    choices_[answer]+="<br>"
                        else:
                            choices_[detail.answer]+=" "+detail.stu.name
                            if len(choices_[detail.answer].split())%2==0:
                                choices_[detail.answer]+="<br>"
                x_data = ['A', 'B', 'C', 'D']
                item_colors = []
                correct_item =  answers[str(serial_No)]              
                b_num = choices[correct_item]
                b_percent = round((b_num / total_num)*100, 1)
                if len(correct_item)==1:
                    markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(value=f'{b_percent}',coord=[correct_item,choices[correct_item]], name="正确率",itemstyle_opts=opts.ItemStyleOpts(color="#55ff37" if b_percent > 70 else "#dbff5e" if b_percent>60 else "#feaf2c" if  b_percent>50 else "red" ))])
                else:
                    markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(value=f'{round((choices[item] / total_num)*100, 1)}',coord=[item,choices[item]], name="正确率",itemstyle_opts=opts.ItemStyleOpts(color="#55ff37" if round((choices[item] / total_num)*100, 1) > 70 else "#dbff5e" if round((choices[item] / total_num)*100, 1)>60 else "#feaf2c" if  round((choices[item] / total_num)*100, 1)>50 else "red" )) for item in correct_item])
                
                bar_chart = (
                    Bar(init_opts=opts.InitOpts(width='150px', height='300px')) #设置图表大小
                    .add_xaxis(x_data)                   
                    .add_yaxis(f'第 {serial_No}题：', [{'value':choices["A"],'text':choices_["A"]},{'value':choices["B"],'text':choices_["B"]},{'value':choices["C"],'text':choices_["C"]},{'value':choices["D"],'text':choices_["D"]}],color='#004080',
                            markpoint_opts= markpoint_opts
                            )
                    #当鼠标移到柱形图的柱体上时，显示柱体表示的选项的选择人员名单，选择人员名单数据在choices_字典中,提示框大小设置为自适应换行
                    .set_global_opts(title_opts=opts.TitleOpts(subtitle=f'{difficult.query.filter(difficult.id==tags[serial_No-1]).first().difficult}'),
                                    tooltip_opts=opts.TooltipOpts(trigger="axis",formatter= JsCode("function (params) { return params[0].data.text;}")),)
                    )
            else:                
                mark=int(json.loads(job_.no_multiple_choice_infor)[str(serial_No)]["分值"])
                bins=[x for x in range(0,mark+1,2)]
                if bins[-1]<mark:
                    bins.append(mark)
                label=[]
                for i in range(1,len(bins)):
                    if i==1:
                        label.append("<="+str(bins[i]))
                    else:
                        if bins[i-1]+1==bins[i]:
                            label.append(str(bins[i]))
                        else:
                            label.append(str(bins[i-1]+1)+"-"+str(bins[i]))
                score_range = pd.cut([job.mark for job in details if job.mark != None], bins=bins, labels=label)
                score_counts = pd.Series(pd.Categorical(score_range, categories=label)).value_counts()                
                score_percentages = [(count / len(details)) * 100 for count in score_counts]
                bar_chart = (
                        Pie(init_opts=opts.InitOpts(width='150px', height='300px'))
                        .add('', list(zip(score_counts.index.tolist(), score_percentages)))
                        .set_global_opts(title_opts=opts.TitleOpts(title=f'第 {serial_No}题：',subtitle=f'{difficult.query.filter(difficult.id==tags[serial_No-1]).first().difficult}'),legend_opts=opts.LegendOpts(pos_right='right'))
                        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {d}%")))
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
    mode=0
    job_=job.query.filter(job.id==job_id).first() 
    select_answer=json.loads(job_.select_answer)
    no_select_infor=json.loads(job_.no_multiple_choice_infor)
    cla = job_class.query.filter(job_class.job_id==job_id).all()
    if not job_ or job_.subject!=current_user.teacher.subject:
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
        mode=request.form.get("mod")
        class_=class_info.query.filter(class_info.id== class_id).first()
        j_c=job_class.query.filter(job_class.job_id==job_id,job_class.class_id==class_id).first()       
    else:
        class_=class_info.query.filter(class_info.id==classes_[0].class_id).first()
        j_c=job_class.query.filter(job_class.job_id==job_id,job_class.class_id==classes_[0].class_id).first()
    if class_:
        jobs = db.session.query(job_student).join(student).join(class_student).filter(class_student.class_id == class_.id,job_student.job_id==job_id).order_by(cast(job_student.mark, db.Float).desc()).all()
    else:
        jobs=[]
    sum_=job_.total1
    f = len([j.mark for j in jobs if j.select_mark==None])
    class_names = [data.class_info.class_name for data in cla]
    max_scores = [data.max for data in cla]
    min_scores = [data.min for data in cla if data !=None]
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
            title_opts=opts.TitleOpts(title="《{}》".format(job_.job_name)),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
            yaxis_opts=opts.AxisOpts(min_=0, max_=sum_),
        )
    )
    js={}
    answers_dict={}
    for i in jobs:
        jt=job_detail.query.filter(job_detail.job_id==i.job_id,job_detail.student==i.student)
        data={}
        data["number"]=str(i.student)
        data["name"]=i.stu_.name 
        data1=[]
        dict={"A":0,"B":1,"C":2,"D":3}
        
        
        for j in select_answer.keys(): 
            jt_= jt.filter(job_detail.serial_No==j).first()                 
            if jt_:
                data[j]=jt_.answer
                if  jt_.mark!=None and jt_.mark>0:
                    data1.append(None)                    
                else:
                    data1.append(dict[jt_.answer[0]])
            else:
                data1.append(None)
        for j in no_select_infor.keys():
            jt_= jt.filter(job_detail.serial_No==j).first()                 
            if jt_:
                data[j]=jt_.mark
            else:
                data[j]=None
        data["select_mark"]=i.select_mark
        data["complete_mark"]=i.complete_mark
        data["mark"]=i.mark
        js[i.id]=data
        answers_dict[i.id]=data1
    #将字典转换为dataframe,当长度不一致时，用NaN填充
    df=pd.DataFrame.from_dict(answers_dict,orient='index')
    #添加总分列，制为每道题分数之和
    #li=[i for i in range(job_.select)]
    similar_pairs = []
    heat=""  
    if mode=="1":
        if not df.empty: 
            #df=df.sort_values(by=li[::-1],ascending=False) #对df按照每道题的分数排序，分数高的在前面如果分数相同，按照下列的分数排序，依次类推
            df.fillna(5,inplace=True)
            df2=df.T
            #计算相似度,若答案为4,则不计算相似度
            similarity=df2.corr(method='pearson')
            #将相似度矩阵转换为列表，每个元素是一个三元组，表示行索引，列索引，相似度
            x=[]
            y=[]
            a=0
            b=0
            for i in range(len(similarity)):
                for j in range(i+1,len(similarity)):
                    if similarity.iloc[i,j]>0.9:
                        similar_pairs.append([a,b,similarity.iloc[i,j]])
                        #将相似度大于0.9的学生的姓名存入x,y列表中                        
                        x.append(js[similarity.index[i]]["name"])
                        y.append(js[similarity.columns[j]]["name"])
                        a+=1
                        b+=1
            #根据相似度，创建热力图,x轴为学生，y轴为学生，颜色越深，相似度越高，similarity的index为学生学号，columns为学生学号，values为相似度
            c = (#图像大小为页面大小
                HeatMap(init_opts=opts.InitOpts(width="100%",height="600px"))
                .add_xaxis(x)
                .add_yaxis("相似度", y, similar_pairs)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="《{}》学生答案相似度".format(job_.job_name)),
                    visualmap_opts=opts.VisualMapOpts(max_=1,min_=0.9),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
                )
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                )
            heat=c.render_embed()
    charts=bar.render_embed()
    dict={'id':job_id,"name":job_.job_name,"select":select_answer,"publish_time":job_.publish_time,"sum":sum_,"n_sub":f,'no_select':no_select_infor}
    return(render_template("job/job_info.html",dict=dict,classes_=classes_,class_=class_,js=js,df=df,j_c=j_c,charts=charts,heat=heat))

#显示学生答题卡，用于核对系统扫描阅卷结果
@job_manage.route("/show_student_card/<id_number>",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def show_student_card(id_number):
    job_id=id_number.split("_")[0]
    number=id_number.split("_")[1]
    job_=job.query.filter(job.id==job_id).first()
    if not job_:
        return("该作业不存在")
    path=os.path.join(os.getcwd(),"app","static","job","job_readed","%s" %job_id,"%s.png" %number)
    answers={}
    if os.path.exists(path):
        #打开作业标准答题卡
        original= judge.open_answer_card(os.path.join(os.getcwd(),"app","static","job","answerCard",job_.paper_url))
        #打开学生答题卡
        img= judge.open_student_card(path)
        n=judge.n
        #调整图片
        img=judge.paper_ajust(original,img)
        pict=judge.pict(img)
        #识别学号
        num_img=pict[16*n:36*n,27*n:67*n]
        #找出学号轮廓
        cnts,h=cv2.findContours(num_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #调整cnts位置，匹配原图img
        cnts=[cnt+np.array([27*n,16*n]) for cnt in cnts]
        #将学号框出来
        cv2.drawContours(img,cnts,-1,(0,0,255),2)
        #识别选择题
        multi=job_.multiple_choice_infor
        multi=json.loads(multi)
        msg,answers=multiple_choice_judge(img,job_id)
        select_answer=json.loads(job_.select_answer)
        if msg !="success":
            return("阅卷错误，请联系管理员")
        for i in multi:
            posi=i["位置"]
            #根据位置信息，找出选择题的轮廓
            t=pict[posi['start']*n:posi['end']*n,6*n:77*n]
            cnts,h=cv2.findContours(t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            #调整cnts位置，匹配原图img
            cnts=[cnt+np.array([6*n,posi['start']*n]) for cnt in cnts]
            #将选择题框出来
            cv2.drawContours(img,cnts,-1,(0,0,255),2)
            
            #将答案写到试卷上
            for j in range(i["初始题号"],i["初始题号"]+i["题目数量"]):
                if j in answers.keys():
                    if answers[j][0]==select_answer[str(j)]:
                        cv2.putText(img,answers[j][0],((j-i["初始题号"])%4*15*n+6*n,(posi['start']+(j-i["初始题号"])//4*2)*n+n),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
                    else:
                        cv2.putText(img,answers[j][0],((j-i["初始题号"])%4*15*n+6*n,(posi['start']+(j-i["初始题号"])//4*2)*n+n),cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),2)
                    
        #将图片转换为base64编码
        img=cv2.imencode('.png',img)[1]
        base64_str = base64.b64encode(img)
        return (render_template("job/show_student_card.html",student_card=base64_str.decode(),answers=answers,student_id=number,job_id=job_id))

#更新阅卷信息
@job_manage.route("/update/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def update():
    if request.method=="POST":
        data=request.get_json()
        job_id=data["job_id"]
        job_=job.query.filter(job.id==job_id).first()
        student_id=data["student_id"]
        job_student_=job_student.query.filter(job_student.job_id==job_id,job_student.student==student_id).first()
        answers=data["answers"]
        update_select_info(student_id,job_id,answers)
        update_class_info(job_id)
        return("success")
    else:
        return("没有提交数据")
        
@job_manage.route("/show_paper/<url>",methods=["POST","GET"]) #显示问卷
@login_required 
@permission_required(Permission.job_publish)
def show_paper(url):
    filename=os.path.join(os.getcwd(),'app',"static","job","paper",'question_paper',current_user.teacher.subject,url)
    #将filename转换为html
    with open(filename, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)
        html = result.value
    return(render_template("job/show_paper.html",html=html,url=url))

@job_manage.route('/show_file/<path:filename>')
@login_required 
@permission_required(Permission.job_publish)
def show_file(filename):
    path=os.path.join(os.getcwd(),'app',"static","paper",'question_paper',current_user.teacher.subject)
    return send_from_directory(path,filename)

@job_manage.route("/create_paper",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def create_paper():
    data={}
    data["status"]=0
    if request.method == "POST":        
        title=request.form.get("title") 
        if job.query.filter(job.job_name==title).first():
            data["status"]+=1
            data["%s" %data["status"]]="已存在该作业"
            return(data)
        number = request.form.get("number")        
        select = request.form.get("select")
        subtopic =request.form.get("subtopic")
        subtopic=json.loads(subtopic)
        c_mark=json.loads(request.form.get("c_mark"))            
        teacher = current_user.realname
        publish_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        publisher=current_user.id            
        file=request.files.get("file")            
        #deadline =datetime.datetime.strptime(deadline,"/%Y/%m/%d")             
        g=request.form.get("grade") 
        g=json.loads(g)

        if current_user.role.has_permission(Permission.job_publish): 
            teacher = current_user.teacher.id
            subject=current_user.teacher.subject
        s_answer=request.form.get("answers")
        tags=request.form.get("tags")
        tags=json.loads(tags)
        r=creat_paper.paper(subject,current_user.realname,2000,title,int(select),subtopic)
        url =str(teacher)+"-"+str(time.time())+".png"
        path=os.path.join(os.getcwd(),"app","static","job","paper","excercise",url)
        if not r[-1]:
            data["status"]=1                
            data["1"]="生成答题卡失败，题目过多，超出卷面"
            return(data)                  
        r[1].save(path) 
        path=os.path.join(os.getcwd(),"app","static","job","paper","question_paper",subject) 
        if not os.path.exists(path): 
            os.makedirs(path)            
        file_ext = file.filename.rsplit('.', 1)[1] # 获取文件扩展名
        filename = title +"."+ file_ext
        path=os.path.join(path,filename)
        file.save(path)
        job_submit = job(job_name=title,publish_time=publish_time,publisher=publisher,question_paper=filename,subject=subject,select_answer=s_answer,context=json.dumps(tags),paper_url=url,s_m=int(number),complete=json.dumps(c_mark),line=json.dumps(r[0]),select=int(select))
        db.session.add(job_submit)
        db.session.flush()
        path=os.path.join(os.getcwd(),"app","static","job","answer",str(job_submit.id))
        path1=os.path.join(os.getcwd(),"app","static","job","job_readed",str(job_submit.id))
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path1):
            os.makedirs(path1)
        if g:
            class_list=db.session.query(class_info).join(grade_info).filter(grade_info.id.in_(g)).filter(class_info.attribute=="行政班").all()    
        else:          
            class_list=db.session.query(class_info).filter(class_info.id.in_(json.loads(request.form.get("classlist")))).all()
        #print(json.loads(request.form.get("classlist")))
        if class_list:  # 作业布置 
            for i in class_list:                    
                check_job=job_class.query.join(job,job_class.job).filter(job.job_name==title,job_class.class_id==i.id,job.subject==current_user.teacher.subject).first()  #避免重复布置相同作业
                if check_job:
                    data["status"]+=1
                    data["%s" %data["status"]]="%s班已经有名为《%s》的作业！" %(check_job.class_info.class_name,title)
                else:
                    job_publish = job_class(class_id=i.id,job_id=job_submit.id)
                    db.session.add(job_publish)
                    db.session.flush()
                    for j in i.students:
                        j_stu=job_student(job_id=job_submit.id,student=j.number)
                        db.session.add(j_stu)
                        db.session.flush()
        else:            
            data["status"]+=1
            data["%s" %data["status"]]="没有设置班级"
        data["url"]="/static/paper/excercise/"+url
        db.session.commit()        
    else:
        data["status"]+=1
        data["%s" %data["status"]]="没有提交作业数据"
    return(data)

"""@job_manage.route("/genarate_paper",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def genarate_paper():
    diff=difficult.query.all()
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
    return(render_template("job/genarate_paper.html",g=g,difficult=diff,class_=class_,Permission=Permission))"""

@job_manage.route("/del/",methods=["POST"])
@login_required 
@permission_required(Permission.job_publish)
def del_job():
    url=request.form.get("url")
    try:
        job_=job.query.filter(job.id==url.split(".")[0]).first()
        path=os.path.join(os.getcwd(),"app","static","job","paper","excercise",job_.paper_url)
        if os.path.exists(path):
            os.remove(path)
        abnormal=abnormal_job.query.filter(abnormal_job.job_id==job_.id).all()
        for i in abnormal:
            db.session.delete(i)
        db.session.flush()       
        db.session.delete(job_)
        db.session.flush()
        db.session.commit()
        return("已删除该作业")
    except Exception as e:
        #显示错误信息
        print(e)
        db.session.rollback()
        return("删除作业失败")

@job_manage.route("/upload/<id>",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_submit)
def upload_paper(id):
    if request.method == 'POST':
        if id=="all":
            url=os.path.join(os.getcwd(),"app","static","job","answer","all",str(current_user.id))
        else:       
            url=os.path.join(os.getcwd(),"app","static","job","answer",str(id))
        
        if not os.path.exists(url):
            os.makedirs(url)
        files = request.files.getlist("files")
        n=0
        for file in files:            
            filename=secure_filename(file.filename)
            
            img= Image.open(file.stream)
            # 将 PIL 图像转换为 numpy 数组
            img_np = np.array(img)
            # 将 RGB 图像转换为 BGR 图像
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            tag,img=judge.find_paper(img_bgr)
            #保存img
            save_path=os.path.join(os.getcwd(),url, filename)
            cv2.imwrite(save_path,img)
            n+=1
                                  
        count=len(os.listdir(url))
        return(jsonify([n,count]))

@job_manage.route("/GetCardFromCamera/<id>",methods=["POST","GET"])  #
@login_required
@permission_required(Permission.job_submit)
def GetCardFromCamera(id):
    if request.method=="POST":
        url=os.path.join(os.getcwd(),"app","static","job","answer",str(id))
        if not os.path.exists(url):
            os.makedirs(url)
        img=request.form.get("img")
        img=base64.b64decode(img)
        img = Image.open(io.BytesIO(img))
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        tag,img=judge.find_paper(img_bgr)
        filename=str(current_user.id)+"_"+str(time.time())+".png"
        save_path=os.path.join(os.getcwd(),url, filename)
        cv2.imwrite(save_path,img)
        return(jsonify("success"))
    return(render_template("/job/camera.html"))
@job_manage.route("/judge/<id>",methods=["POST","GET"]) #
@login_required 
@permission_required(Permission.job_submit)
def job_judge(id):
    path=os.path.join(os.getcwd(),"app","static","job","answer",str(id))
    #遍历path文件夹下的所有文件
    files=os.listdir(path)
    n=0
    #如果path文件夹下没有文件，则返回
    if not files:
        return("没有作业需要阅卷")
    for i in files:
        #获取文件的绝对路径
        file=os.path.join(path,i)
        #判断是否是文件夹
        path1=os.path.join(os.getcwd(),"app","static","job","abnormal_paper",str(id))
        if not os.path.exists(path1):
            os.makedirs(path1)
        if not os.path.isdir(file):
            standard=judge.open_answer_card(os.path.join(os.getcwd(),"app","static","job","answerCard","%s.png" %id))
            img=judge.open_student_card(file)
            img=judge.paper_ajust(standard,img)
            messeage=judge.qr_recognize(img,(judge.n*15,judge.n*37,judge.n*66,judge.n*82))
            if not messeage:
                #旋转180度
                img1=cv2.rotate(img,cv2.ROTATE_180)
                messeage=judge.qr_recognize(img1,(judge.n*15,judge.n*37,judge.n*66,judge.n*82))
                """if not messeage:
                    #异常卷移至abnormal_paper文件夹中
                    os.rename(file,os.path.join(path1,i))
                    abnormal=abnormal_job(job_id=id,reason="二维码识别失败",paper=i,teacher_id=current_user.teacher.id,time=datetime.datetime.now())
                    db.session.add(abnormal)
                    db.session.flush()
                    db.session.commit()
                    continue"""
            if messeage:
                print(messeage)
                if messeage[0].split("_")[0]!=str(id):
                    #异常卷移至abnormal_paper文件夹中
                    os.rename(file,os.path.join(path1,i))
                    abnormal=abnormal_job(job_id=id,reason="二维码信息不匹配",paper=i,teacher_id=current_user.teacher.id,time=datetime.datetime.now())
                    db.session.add(abnormal)
                    db.session.flush()
                    db.session.commit()
                    continue
            else:
                print("二维码识别失败")
            number=judge.number_pos(img)
            msg=check_student_number(number,id)                       
            if msg !="success":
                #将异常卷的信息存入abnormal_job表中
                ab=abnormal_job(job_id=int(id),paper=i,student_id=number,reason=msg,teacher_id=current_user.teacher.id,time=datetime.datetime.now())
                db.session.add(ab)
                db.session.flush()
                #将异常卷移至abnormal_paper文件夹中
                os.rename(file,os.path.join(path1,i))
                db.session.commit()
                continue
            else:
                msg1,mark=multiple_choice_judge(img,id)
                if msg1!="success":
                    ab=abnormal_job(job_id=id,paper=i,student_id=number,reason=msg1,teacher_id=current_user.teacher.id,time=datetime.datetime.now())
                    db.session.add(ab)
                    db.session.flush()
                    #将异常卷移至abnormal_paper文件夹中
                    os.rename(file,os.path.join(path1,i))
                    db.session.commit()
                    if msg1=="作业不存在":
                        continue                
                se=update_select_info(number,id,mark)
                j_stu=job_student.query.filter(job_student.job_id==int(id),job_student.student==number).first()
                j_stu.select_mark=se
                j_stu.submit_time=datetime.datetime.now()
                n+=1
            #将已经阅卷的卷子移至job_readed文件夹中,并修改文件名            
            if msg=="success" and msg1=="success":
                path1=os.path.join(os.getcwd(),"app","static","job","job_readed",str(id))
                if not os.path.exists(path1):
                    os.makedirs(path1)
                path2=os.path.join(path1,str(number)+".png")
                os.rename(file,path2)
            #生成非选择题阅卷信息
            non_multiple_choice_to_read(number,id)
    update_class_info(id)
    db.session.commit()
    return(jsonify("成功阅卷%s份" %n))

@job_manage.route("/show_answer/<id>",methods=["POST","GET"]) #
@login_required 
@permission_required(Permission.job_publish)
def show_answer(id):
    job_=job.query.filter(job.id==id).first().select_answer
    return jsonify(job_)

@job_manage.route("/get_cpl_title_number/",methods=["POST","GET"]) #
@login_required 
@permission_required(Permission.job_publish)
def get_title_number():
    if request.method=="POST":
        id=request.form.get("id")
        j=job.query.filter(job.id==id).first()
        if not j:
            return("没有该作业")
        cpl=json.loads(j.no_multiple_choice_infor)
        title_number=[]
        for k in cpl.keys():
            title_number.append(k)        
        return(jsonify(title_number))


@job_manage.route("/cpl_judge/",methods=["POST","GET"]) #填空题阅卷
@login_required 
@permission_required(Permission.job_publish)
def cpl_judge():
    if request.method=="POST":
        id=request.form.get("id")
        title_number=request.form.get("title_number")
        stu=request.form.get("stu")
        j=job.query.filter(job.id==id).first()        
        if not j:
            return("没有该作业")
        complete=json.loads(j.no_multiple_choice_infor)
        if not stu:
            j_detail=job_detail.query.join(student).join(class_student).join(class_info).join(teaching_information)\
                .filter(job_detail.job_id==id)\
                .filter(job_detail.student==student.number)\
                .filter(student.id==class_student.student_id)\
                .filter(class_student.class_id==class_info.id)\
                .filter(class_info.id==teaching_information.class_id)\
                .filter(teaching_information.teacher_id==current_user.teacher.id)\
                .filter(job_detail.serial_No==title_number,job_detail.mark==None)\
                .order_by(job_detail.serial_No).first()
        else:
            #找出job_detail的 job_id==id,serial_No==title_number的记录中，student like stu或者 stu.name like stu的记录
            j_detail=job_detail.query.join(student).join(class_student).join(class_info).join(teaching_information)\
                .filter(job_detail.job_id==id)\
                .filter(job_detail.student==student.number)\
                .filter(student.id==class_student.student_id)\
                .filter(class_student.class_id==class_info.id)\
                .filter(class_info.id==teaching_information.class_id)\
                .filter(teaching_information.teacher_id==current_user.teacher.id)\
                .filter(job_detail.serial_No==title_number)\
                .filter(or_(student.number.like("%"+stu+"%"),student.name.like("%"+stu+"%")))\
                .order_by(job_detail.serial_No).first()
        if j_detail:
            paper =os.path.join(os.getcwd(),"app","static","job","job_readed",str(id),j_detail.student+".png")            
            if os.path.exists(paper):
                answer_card=os.path.join(os.getcwd(),"app","static","job","answerCard",j.paper_url)
                
                img=judge.open_answer_card(answer_card)
                ep =judge.open_student_card(paper)
                ep=judge.paper_ajust(img,ep)
                #if judge.qr(img)==judge.qr(ep):
                infor=json.loads(j.no_multiple_choice_infor)
                n=judge.n                
                img=ep[infor[title_number]["位置"]["start"]*n:infor[title_number]["位置"]["end"]*n,7*n:75*n]               
                retval, buffer = cv2.imencode('.png', img)
                # 创建响应对象
                img_b64 = base64.b64encode(buffer).decode('utf-8')
                stu=student.query.filter(student.number==j_detail.student).first().name
                response = {'image': img_b64,'No':j_detail.serial_No,'mark':infor[title_number]["分值"],'id':j_detail.id,'name':stu}
                response['Content-Type'] = 'image/png'
                return jsonify(response)
            else:
                paper1=os.path.join(os.getcwd(),"app","static","job","abnormal_paper",str(id),j_detail.student+".png")
                if os.path.exists(paper1):
                    img=judge.open(os.path.join(os.getcwd(),"app","static","job","paper","excercise",j.paper_url))
                    ep =judge.open2(paper1)
                    ep=judge.paper_ajust(img,ep)
                    #if judge.qr(img)==judge.qr(ep):
                    split=judge.paper_split(ep,select,json.loads(j.line))
                    retval, buffer = cv2.imencode('.png', split[-1][j_detail.serial_No-select-1])
                    # 创建响应对象
                    img_b64 = base64.b64encode(buffer).decode('utf-8')
                    stu=student.query.filter(student.number==j_detail.student).first().name
                    response = {'image': img_b64,'No':j_detail.serial_No,'mark':json.loads(j.complete)[j_detail.serial_No-j.select-1],'id':j_detail.id,'name':stu}
                    response['Content-Type'] = 'image/png'
                    return jsonify(response)
                else:
                    img=None
                    response= make_response("试卷不存在")
                    response.headers['Content-Type'] = 'text/plain' 
            #计算图片的非白色像素点的个数
            if img:
                count = cv2.countNonZero(img)
                #计算图片的像素点总个数
                size = img.size
                             
        else:
            response= make_response("无待阅卷")
            response.headers['Content-Type'] = 'text/plain'
        return(response)

@job_manage.route("/set_cpl_mark/",methods=["POST"]) #
@login_required 
@permission_required(Permission.job_publish)
def set_cpl_mark():
    if request.method=="POST":
        id=request.json["id"]
        mark=request.json["mark"]
        serial_No=request.json["title_number"]       
        j_t=job_detail.query.filter(job_detail.id==id,job_detail.serial_No==serial_No).first()
        j_stu=job_student.query.filter(job_student.job_id==j_t.job_id,job_student.student==j_t.student).first()
        if j_t:
            j_t.mark=mark
            if j_stu.complete_mark:
                j_stu.complete_mark+=mark
            else:
                j_stu.complete_mark=mark
            db.session.flush()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                return(Exception)
            return(jsonify(j_t.job_id))
        else:
            return("找不到该作业")
        
@job_manage.route("/judge_report/<id>",methods=["POST","GET"]) #阅卷报告
@login_required
@permission_required(Permission.job_publish)
def judge_report(id):
    if id == "this":
        d_judge=abnormal_job.query.filter(abnormal_job.teacher_id==current_user.teacher.id).all()
        #筛选出当前教师所任教班级的所有作业
        this=job_student.query.join(student).join(class_student).join(class_info).join(teaching_information).filter(class_info.id==teaching_information.class_id).filter(teaching_information.teacher_id==current_user.teacher.id).filter(job_student.submit_time>datetime.datetime.now()-datetime.timedelta(minutes=5)).filter(job_student.mark!=None).count()
        all=job_student.query.join(student).join(class_student).join(class_info).join(teaching_information).filter(class_info.id==teaching_information.class_id).filter(teaching_information.teacher_id==current_user.teacher.id).filter(job_student.mark!=None).count()
    elif id=="all":
        d_judge=abnormal_job.query.filter(abnormal_job.teacher_id==current_user.teacher.id).all()
        this=job_student.query.join(student).join(class_student).join(class_info).join(teaching_information).filter(class_info.id==teaching_information.class_id).filter(teaching_information.teacher_id==current_user.teacher.id).filter(job_student.submit_time>datetime.datetime.now()-datetime.timedelta(minutes=5)).filter(job_student.mark!=None).count()
        all=job_student.query.join(student).join(class_student).join(class_info).join(teaching_information).filter(class_info.id==teaching_information.class_id).filter(teaching_information.teacher_id==current_user.teacher.id).filter(job_student.mark!=None).count()
    #判断id是否为数字，如果是数字，则为作业id，否则为all或者this
    elif id.isdigit():
        d_judge=abnormal_job.query.filter(abnormal_job.job_id==id,abnormal_job.teacher_id==current_user.teacher.id).all()

        job_=job.query.filter(job.id==id).first()
        #n为提交时间为一个小时之内的job_student记录数
        this=job_student.query.join(student).join(class_student).join(class_info).join(teaching_information).filter(class_info.id==teaching_information.class_id).filter(teaching_information.teacher_id==current_user.teacher.id).filter(job_student.submit_time>datetime.datetime.now()-datetime.timedelta(minutes=5)).filter(job_student.mark!=None).filter(job_student.job_id==int(id)).count()
        all=job_student.query.join(student).join(class_student).join(class_info).join(teaching_information).filter(class_info.id==teaching_information.class_id).filter(teaching_information.teacher_id==current_user.teacher.id).filter(job_student.mark!=None).filter(job_student.job_id==int(id)).count()
    else:
        return("没有相关作业")
    data=[[d.id,d.reason,d.paper,d.student_id] for d in d_judge]
    data={"s_num":this,"d_num":len(data),"name":job_.job_name,"total":all,"d_list":data}
    return render_template("job/judge_report.html",data=data,id=id)

@job_manage.route("/clear_abnormal/<id>",methods=["POST","GET"]) #阅卷报告
@login_required
@permission_required(Permission.job_publish)
def clear_abnormal(id):
    if request.method=="POST":
        #data为后台传来的json数据，是一个列表,存储了要删除的异常记录的paper字段的值
        data=request.json
        n=0
        for d in data:
            abnormal_job.query.filter(abnormal_job.paper==d).delete()
            #删除异常异常卷图片
            path=os.path.join(os.getcwd(),"app","static","job","abnormal_paper",str(id),d)
            if os.path.exists(path):
                os.remove(path)
            n+=1
        db.session.flush()
        db.session.commit()
        d_judge=abnormal_job.query.filter(or_(abnormal_job.student_id==None,abnormal_job.student_id.in_(db.session.query(class_student.student_id).filter(class_student.class_id.in_(db.session.query(teaching_information.class_id).filter(teaching_information.teacher_id==current_user.id)))))).filter(abnormal_job.job_id==id).all()
    data=[[d.id,d.reason,d.paper,d.student_id] for d in d_judge]
    total=job_student.query.filter(job_student.job_id==int(id)).filter(job_student.mark!=None).count()
    name=job.query.filter(job.id==id).first().job_name
    return(jsonify({"s_num":n,"d_num":len(data),"name":name,"total":total,"d_list":data}))

@job_manage.route("/abnormal/<args>",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def abnormal(args):
    job_id,ab_id=args.split(":")
    job_=job.query.filter(job.id==job_id).first()
    abn=abnormal_job.query.filter(abnormal_job.id==ab_id).first()
    path1=os.path.join(os.getcwd(),"app","static","job","answerCard",job_.paper_url)
    path2=os.path.join(os.getcwd(),"app","static","job","abnormal_paper",str(job_id),abn.paper)
    if not os.path.exists(path1):
        return("作业不存在") 
    if not os.path.exists(path2):
        return("学生答题卡不存在,请返回")
    img=judge.open_answer_card (path1)
    pict=judge.open_student_card(path2)
    pict=judge.paper_ajust(img,pict)
    n=judge.n
    if abn.reason=="二维码识别失败":
        retval, buffer = cv2.imencode('.png', pict)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
    elif "学号" in abn.reason:        
        pict=pict[4*n:36*n,6*n:68*n]        
    elif "选择题" in abn.reason:        
        pict=pict[4*n:36*n,7*n:68*n]
    #使用cv2识别出pict中的黑色方快，并将其描边为红色
    if '选择题' in abn.reason or '学号' in abn.reason:
        cnts=judge.pict(pict)        
        cnt,h=cv2.findContours(cnts,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        pict=cv2.drawContours(pict,cnt,-1,(0,0,255),2)
    
    retval, buffer = cv2.imencode('.png', pict)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    return render_template("job/abnormal.html",img=img_b64,job=job_,abnormal=abn)
   
@job_manage.route("/JudgeErroHanding/modifyNumber/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def modifyNumber():
    if request.method=="POST":
        id=request.form.get("id")
        paper=request.form.get("paper")
        number=request.form.get("number")
        print("------------------" ,paper,number)
        ab=abnormal_job.query.filter(abnormal_job.id==id).first()
        paper=os.path.join(os.getcwd(),'app','static','job',paper) 
        print(paper)   
        msg=judgeWithNumber(number,paper,ab.job_id)
        if msg!="success":
            if ab.paper==paper.split("/")[-1]:
                ab.reason=msg
            else:
                ab1=abnormal_job(job_id=ab.job_id,reason=msg,paper=paper.split("/")[-1],teacher_id=current_user.teacher.id,time=datetime.datetime.now())
                db.session.add(ab1)
        else:
            #删除abs
            if ab.paper==paper.split("/")[-1]:
                db.session.delete(ab)
            else:
                paper=os.path.join(os.getcwd(),'app','static','job','abnormal_paper',str(ab.job_id),ab.paper)
                msg=judgeWithNumber(ab.student_id,paper,ab.job_id)
                if msg!="success":
                    ab.reason=msg
                else:
                    db.session.delete(ab)
        db.session.flush()
        db.session.commit()
        return(msg)

@job_manage.route("/JudgeErroHanding/Assignjob/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def Assignjob():
    if request.method=="POST":
        id=request.form.get("id")
        job_id=request.form.get("job_id")
        student_id=request.form.get("student_id")
        ab=abnormal_job.query.filter(abnormal_job.id==id).first()
        j_s=job_student.query.filter(job_student.job_id==job_id,job_student.student==student_id).first()
        if j_s:
            msg="该学生已经有名为《%s》的作业任务" %job.query.filter(job.id==job_id).first().job_name
        else:
            j_s=job_student(job_id=job_id,student=student_id)
            db.session.add(j_s)
            db.session.flush()
            msg="已为学号为%s的学生布置名为《%s》的作业任务" %(student_id,job.query.filter(job.id==job_id).first().job_name)
        msg1=judgeWithNumber(student_id,os.path.join(os.getcwd(),'app','static','job','abnormal_paper',str(job_id),ab.paper),job_id)
        #如果msg1不为success，则将异常卷的原因改为msg1,否则删除abnormal_job表中的记录
        if msg1!="success":
            ab.reason=msg1
            ab.student_id=student_id
            ab.job_id=job_id
        else:
            db.session.delete(ab)
        db.session.flush()
        db.session.commit()
        return(msg,msg1)

def judgeWithNumber(number,paper,job_id):
    j_stu=job_student.query.filter(job_student.job_id==int(job_id),job_student.student==number).first()
    if not j_stu:
        return("学号为:%s的学生没有名为《%s》的作业任务" %(number ,job.query.filter(job.id==job_id).first().job_name))  
    card=os.path.join(os.getcwd(),'app','static','job','answerCard',job.query.filter(job.id==job_id).first().paper_url)
    img=judge.open_student_card(paper)
    img=judge.paper_ajust(judge.open_answer_card(card),img)
    msg1,mark=multiple_choice_judge(img,job_id)
    
    if msg1=="作业不存在":   
        return msg1        
    se=update_select_info(number,job_id,mark)    
    j_stu.select_mark=se
    j_stu.submit_time=datetime.datetime.now()
    if msg1=="success":
#将已经阅卷的卷子移至job_readed文件夹中,并修改文件名    
        path1=os.path.join(os.getcwd(),"app","static","job","job_readed",str(job_id))
        if not os.path.exists(path1):
            os.makedirs(path1)
        path2=os.path.join(path1,str(number)+".png")
        os.rename(paper,path2)
    #生成非选择题阅卷信息
    non_multiple_choice_to_read(number,job_id)
    update_class_info(job_id)
    db.session.flush()
    db.session.commit()
    return(msg1)

@job_manage.route("func1",methods=["POST","GET"])
def func1():
    #获取当前用户的行政班任教信息
    t_info=teaching_information.query.join(class_info).filter(teaching_information.teacher_id==current_user.teacher.id,class_info.attribute=="行政班").all()
    #获取当前用户所在学科的所有作业
    jobs=job.query.filter(job.subject==current_user.teacher.subject).all()
    #将每一个作业布置给每一个班级
    for j in jobs:
        for t in t_info:
            j_s=job_class(job_id=j.id,class_id=t.class_id)
            db.session.add(j_s)
            db.session.flush()
    db.session.commit()
    return("ok")

@job_manage.route("/job_analyse",methods=["POST","GET"]) #阅卷报告
@login_required
@permission_required(Permission.job_publish)
def job_analyse():    
    t_info=teaching_information.query.join(class_info).filter(teaching_information.teacher_id==current_user.teacher.id).all()
    classes=[c.class_info for c in t_info]
    end=datetime.date.today()
    start=end-datetime.timedelta(days=7)
    id=None
    job_name=""
    if request.method=="POST":
        start=request.form.get("start")
        end= request.form.get("end")
        id = request.form.get("id")
        job_name=request.form.get("job_name")
    print(job_name)   
    #job_class表中，存储了某班级，某作业的情况，包括作业的平均分，标准差，完成率，找出时间段内，所任教班级的任教学科作业的平均分，完成率，标准差，以pyecharts柱形图呈现
    class_names = [c.class_name for c in classes]
    avg_scores=[]
    completion_rates=[]
    std_devs=[]
    for i in classes:
        #筛选所有job_class表中，class_id==i.id的记录，作业名称包含job_name的，布置时间在start和end之间，学科为当前用户任教学科的作业记录
        job_classes = job_class.query.join(job).filter(job_class.class_id==i.id,job.job_name.like("%"+str(job_name)+"%"),job_class.date.between(start,end),job.subject==current_user.teacher.subject).all() 
        if job_classes:
            avg_scores.append(round(sum([c.average/job.query.filter(job.id==c.job_id).first().total1 for c in job_classes])/len(job_classes)*100,2))
            completion_rates.append(round(sum([c.submit_number/len(class_student.query.filter(class_student.class_id==c.class_id).all()) for c in job_classes])/len(job_classes)*100,2))
            std_devs.append(round(sum([c.std for c in job_classes])/len(job_classes),2))
        else:
            avg_scores.append(0)
            completion_rates.append(0)
            std_devs.append(0)
    bar = (
        Bar()
        .add_xaxis(class_names)
        .add_yaxis("平均得分率", avg_scores)
        .add_yaxis("完成率", completion_rates)
        .add_yaxis("标准差", std_devs)
        .set_global_opts(title_opts=opts.TitleOpts(title="班级作业对比")) 
        #x轴的数据旋转角度
    )
    #查找出所有在所选时间段内，布置给所任教班级的所任教学科的作业，布置时间数据在job_class表date字段中，job_class数据表为作业布置数据表,以布置时间排序
    jobs=job.query.join(job_class).filter(job_class.class_id.in_([c.id for c in classes]),job.job_name.like("%"+str(job_name)+"%"),job.subject==current_user.teacher.subject,job_class.date.between(start,end)).order_by(job_class.date).all()
    #将作业的平均分，完成率，标准差，以pyecharts折线图呈现
    job_names=[j.job_name for j in jobs]
    avg_scores=[]
    completion_rates=[]
    std_devs=[]
    for j in jobs:
        if id:#如果前端传来了班级id，则统计该班级的作业信息，否则，统计所有班级的作业信息
            job_class_=job_class.query.filter(job_class.job_id==j.id,job_class.class_id==int(id)).first()
            if job_class_:
                avg_scores.append(round(job_class_.average/j.total1*100,2))
                completion_rates.append(round(job_class_.submit_number/len(class_student.query.filter(class_student.class_id==job_class_.class_id).all())*100,2))
                std_devs.append(round(job_class_.std,2))
            else:   
                avg_scores.append(0)
                completion_rates.append(0)
                std_devs.append(0)
        else:
            job_classes=job_class.query.filter(job_class.job_id==j.id).all()
            if job_classes:
                if sum([c.submit_number for c in job_classes]):
                    avg_scores.append(round(sum([c.average/j.total1*c.submit_number for c in job_classes])/sum([c.submit_number for c in job_classes])*100,2))               
                    completion_rates.append(round(sum([c.submit_number for c in job_classes] )/sum([len(class_student.query.filter(class_student.class_id==c.class_id).all()) for c in job_classes])*100,2))
                    std_devs.append(round(sum([c.std for c in job_classes])/len(job_classes),2))
                else:
                    completion_rates.append(0)
                    avg_scores.append(0)
                    std_devs.append(0)
            else:
                avg_scores.append(0)
                completion_rates.append(0)
                std_devs.append(0)    
    line = (
        Line(init_opts=opts.InitOpts(width="100%"))
        .add_xaxis(job_names)
        .add_yaxis("平均得分率", avg_scores)
        .add_yaxis("完成率", completion_rates)
        .add_yaxis("标准差", std_devs)
        .set_global_opts(title_opts=opts.TitleOpts(title="所选时段内作业情况变化趋势图"),xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)))   
    )
    return render_template("job/job_analyse.html", classes=classes, chart=bar.render_embed(),chart2=line.render_embed())

@job_manage.route("/modify_mark/<id>",methods=["POST","GET"]) #修改选择题成绩，当选择题分数设置错误，需要整体修改时运行该函数
@login_required
@permission_required(Permission.job_publish)
def modify_mark(id):
    job_=job.query.filter(job.id==id).first()
    mark=job_.s_m
    jt=job_detail.query.filter(job_detail.job_id==id).filter(job_detail.serial_No<=job_.select).all()
    answers=job_.select_answer[:-1].split(" ")
    for j in jt:        
        if j.answer==answers[j.serial_No-1]:
            j.mark=mark
    j_s=job_student.query.filter(job_student.job_id==id).filter(job_student.mark!=None).all()
    for j in j_s:
        #j.mark的值为所有相关job_detail的mark的和
        jt=job_detail.query.filter(job_detail.job_id==id).filter(job_detail.serial_No<=job_.select).filter(job_detail.student==j.student).all()
        j.select_mark=sum([i.mark for i in jt])
    j_cla=job_class.query.filter(job_class.job_id==int(id)).all()  #阅卷完成后统计作业情况，查询被布置了此作业的所有班级
    #分别统计每个班的作业情况，包括提交人数，平均分，最高分，最低分，标准差
    for j in j_cla:
        #job_student有外键student连接到student表，class_student表有外键class_id连接到class_info表,student_id连接到student表,运用join连接查询，获取每个班级的学生作业情况
        # 如果值为空，则设置为0     
        average=db.session.query(func.avg(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #平均分
        submit_number=job_student.query.filter(job_student.job_id==int(id),job_student.mark!=None).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id).count() #提交人数
        max=db.session.query(func.max(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #最高分
        min=db.session.query(func.min(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #最低分
        std=db.session.query(func.stddev(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #标准差
        if average:
            j.average=average
        if submit_number:
            j.submit_number=submit_number
        if max:
            j.max=max
        if min:
            j.min=min
        if std:
            j.std=std
        db.session.flush()    
    db.session.commit()
    return ("chenggong")

@job_manage.route("/modify/<id>",methods=["POST","GET"]) #将异常卷的文件名以学号命名
@login_required
@permission_required(Permission.job_publish)
def modify(id):
    ab=db.session.query(abnormal_job).filter(abnormal_job.job_id==id).all()
    n=0
    for a in ab:
        path=os.path.join(os.getcwd(),"app/static/abnormal_paper",str(id),a.paper)
        
        if os.path.exists(path):
            if a.student_id:
                os.rename(path,os.path.join(os.getcwd(),"app/static/abnormal_paper",str(id),a.student_id+".png"))
                a.paper=a.student_id+".png"
                db.session.flush()
                n+=1
    db.session.commit()
    return(str(n))

@job_manage.route("/class/<id>",methods=["POST","GET"]) 
@login_required
@permission_required(Permission.job_publish)
def student_info(id):
    end=datetime.datetime.now()
    start=end-datetime.timedelta(days=7)
    job_name=""
    if request.method=="POST":
        start=request.form.get("start")
        end=request.form.get("end")   
        job_name=request.form.get("job_name")
        id=request.form.get("class_id")     
    t_info=teaching_information.query.filter(teaching_information.class_id==id,teaching_information.teacher_id==current_user.teacher.id).first()
    if not t_info:
        return("您没有权限查看该班级的学生信息")
    class_=db.session.query(class_info).filter(class_info.id==id).first()
    stu=student.query.join(class_student,student.id==class_student.student_id).filter(class_student.class_id==id).all()
    #查找时间段内,所任教学科布置给该班级的学生的作业
    job_=job.query.join(job_class).filter(job.job_name.like("%"+str(job_name)+"%"),job.subject==current_user.teacher.subject,job_class.class_id == id,job_class.date.between(start,end)).all()
    table=[]
    for s in stu:
        dict={}
        dict["name"]=s.name
        dict["number"]=s.number
        dict["未交作业"]=job_student.query.filter(job_student.job_id.in_([i.id for i in job_]),job_student.student==s.number,job_student.mark==None).count()
        #平均得分率为每个作业的得分，除以该作业的总分，再求平均值，每个作业的总分在job表中的total字段
        scores = []
        for j in job_:
            job_student_ = job_student.query.filter(job_student.job_id==j.id, job_student.student==s.number).first()
            
            if job_student_ is not None  and job_student_.mark is not None and j.total1:
                scores.append(job_student_.mark / j.total1)
        dict["平均得分率"] = round(sum(scores) / len(scores)*100,2) if scores else 0
        table.append(dict)
    df=pd.DataFrame(table)
    #根据平均得分率降序排序
    df=df.sort_values(by="平均得分率",ascending=False)
    return(render_template("/job/class.html",class_=class_,df=df,jobs=len(job_)))

@job_manage.route("/personal/<number>",methods=["POST","GET"]) 
@login_required
@permission_required(Permission.job_publish)
def student_charts(number):
    start=datetime.datetime.now()-datetime.timedelta(days=7)
    end=datetime.datetime.now()
    job_name=""
    if request.method=="POST":
        start=request.form.get("start")
        end=request.form.get("end")
        job_name=request.form.get("job_name")
    #查找学生所处班级    
    class_=class_info.query.join(class_student).join(student).filter(student.number==number).first()
    job_=job.query.join(job_class).filter(job.job_name.like("%"+str(job_name)+"%"),job.subject==current_user.teacher.subject,job_class.class_id == class_.id,job_class.date.between(start,end)).all()
    job_names=[j.job_name for j in job_]
    scores=[]
    average=[]
    name=student.query.filter(student.number==number).first().name
    for j in job_:
        job_student_=job_student.query.filter(job_student.job_id==j.id,job_student.student==number).first()
        if job_student_:
            if job_student_.mark!=None:
                
                scores.append(round(job_student_.mark/j.total1*100,2))  
            else:
                scores.append(0)          
        else:
            scores.append(0)
        job_class_=job_class.query.filter(job_class.job_id==j.id,job_class.class_id==class_.id).first()            
        average.append(round(job_class_.average/j.total1*100,2))
    line=(Line( init_opts=opts.InitOpts(width="100%", height="500px"))
        .add_xaxis(job_names)
        .add_yaxis("得分率",scores)
        .add_yaxis("班级平均得分率",average)
        .set_global_opts(title_opts=opts.TitleOpts(title=name+"作业得分情况"),toolbox_opts=opts.ToolboxOpts(),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-20)),
            yaxis_opts=opts.AxisOpts(min_=0, max_=100)
        )
        )            
    #line图表渲染，通过ajax传送给前
    return (line.render_embed())

@job_manage.route("/genarate_paper",methods=["POST","GET"])  #
@login_required 
@permission_required(Permission.job_publish)
def genarate_paper():
    diff=difficult.query.all()
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
    return(render_template("/job/paper.html",g=g,difficult=diff,class_=class_,Permission=Permission))


@job_manage.route("/paper/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def initial_paper():               
    paper=creat_paper.genarate_papaer(2000)#paper为pil格式图片
    n=paper.width//82       
    creat_paper.number_area(n,paper,n*27,n*9,10)
    paper=creat_paper.paste_image(paper)
    #将paper保存在static文件夹下的temp文件夹中，文件名为currentuser的id，格式为png
    paper.save(os.path.join(os.getcwd(),"app","static","job","temp",str(current_user.id)+".png"))
    #将pil格式图片转换为opencv格式图片
    paper_cv=np.array(paper)
    paper_cv=cv2.cvtColor(paper_cv,cv2.COLOR_RGB2BGR)
    retval, buffer = cv2.imencode('.png', paper_cv)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    # 创建响应对象
    response = make_response(img_b64)
    # 设置响应头
    response.headers['Content-Type'] = 'text/plain'
    return(response)

@job_manage.route("/modifyTitle/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def modifyTitle():
    if request.method=="POST":
        title=request.form.get("title")
        img=Image.open(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        img=creat_paper.add_title(img,title)
        img.save(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        img_cv=np.array(img)
        img_cv=cv2.cvtColor(img_cv,cv2.COLOR_RGB2BGR)
        retval, buffer = cv2.imencode('.png', img_cv)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        # 创建响应对象
        response = make_response(img_b64)
        # 设置响应头
        response.headers['Content-Type'] = 'text/plain'
        return(response)

@job_manage.route("/paper/select",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def drawSelect():
    if request.method=="POST":
        quantity=int(request.form.get("quantity"))
        number1=int(request.form.get("number1"))
        number2=int(request.form.get("number2"))
        score=float(request.form.get("score"))
        position=int(request.form.get("position"))
        checkMultiple=request.form.get('checkMultiple')
        #打开pil图像,图像位置在static文件夹下的temp目录中
        img=Image.open(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        n=img.width//82
        pos=creat_paper.genarate_select(n,number1,number2,quantity,score,img,n*7,n*position,checkMultiple)
        img.save(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        #将pil格式图片转换为opencv格式图片
        img_cv=np.array(img)
        img_cv=cv2.cvtColor(img_cv,cv2.COLOR_RGB2BGR)
        retval, buffer = cv2.imencode('.png', img_cv)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        # 创建响应对象，将pos和img_b64传输给前端
        response = make_response(json.dumps({"pos":pos,"img":img_b64}))
        # 设置响应头
        response.headers['Content-Type'] = 'text/plain'
        return(response)

@job_manage.route("/paper/complete/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def drawComplete():
    if request.method=="POST":
        subtopic=request.form.get("subtopic")
        subtopic=json.loads(subtopic)
        number1=int(request.form.get("number1"))
        number2=int(request.form.get("number2"))
        c_marks=request.form.get("c_mark") 
        c_marks=json.loads(c_marks)       
        position=int(request.form.get("position"))
        #打开pil图像,图像位置在static文件夹下的temp目录中
        img=Image.open(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        n=img.width//82
        pos=creat_paper.generate_completion(n,img,subtopic,c_marks,n*7,n*position,number1,number2)
        img.save(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        #将pil格式图片转换为opencv格式图片
        img_cv=np.array(img)
        img_cv=cv2.cvtColor(img_cv,cv2.COLOR_RGB2BGR)
        retval, buffer = cv2.imencode('.png', img_cv)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        # 创建响应对象，将pos和img_b64传输给前端,pos是一个列表，每个元素是一个字典，包含了每题的开始位置和结束位置
        response = make_response(json.dumps({"pos":pos[0],"img":img_b64}, default=str))
        response.headers['Content-Type'] = 'text/plain'
        return(response)

@job_manage.route("/paper/shortAnswer/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def drawShortAnswer():
    if request.method=="POST":
        line=request.form.get("line")
        line=json.loads(line)
        score=request.form.get("score")
        score=json.loads(score)
        number1=int(request.form.get("number1"))
        number2=int(request.form.get("number2"))
        position=int(request.form.get("position"))
        #打开pil图像,图像位置在static文件夹下的temp目录中
        img=Image.open(os.path.join(os.getcwd(),"app","static","job","temp",str(current_user.id)+".png"))
        n=img.width//82
        pos=creat_paper.drawShortAnswer(n,img,n*position,line,score,number1,number2)
        img.save(os.path.join(os.getcwd(),"app","static","job","temp",str(current_user.id)+".png"))
        #将pil格式图片转换为opencv格式图片
        img_cv=np.array(img)
        img_cv=cv2.cvtColor(img_cv,cv2.COLOR_RGB2BGR)
        retval, buffer = cv2.imencode('.png', img_cv)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        # 创建响应对象，将pos和img_b64传输给前端,pos是一个列表，每个元素是一个字典，包含了每题的开始位置和结束位置
        response = make_response(json.dumps({"pos":pos,"img":img_b64}, default=str))
        response.headers['Content-Type'] = 'text/plain'
        return(response)

@job_manage.route("/paper/rollBack/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def rollback():
    if request.method=="POST":
        #获取后台传来的structrued数据
        structrued=request.form.get("structrued")
        structrued=json.loads(structrued)
        key=structrued.keys()
        last=structrued[list(key)[-1]]
        if "选" in last["类型"]:
            start=last["位置"]["start"]
            end=last["位置"]["end"]
        else:
            key=last["位置"].keys()
            start=last["位置"][list(key)[0]]["start"]
            end=last["位置"][list(key)[-1]]["end"]+1
        #打开pil图像,图像位置在static文件夹下的temp目录中
        img=Image.open(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        #将img的start到end的区域填充为白色
        n=img.width//82
        img=creat_paper.fillWhite(img,(start-3)*n,end*n)
        pos=start-3
        img.save(os.path.join(os.getcwd(),"app/static/job/temp",str(current_user.id)+".png"))
        #将pil格式图片转换为opencv格式图片
        img_cv=np.array(img)
        img_cv=cv2.cvtColor(img_cv,cv2.COLOR_RGB2BGR)
        retval, buffer = cv2.imencode('.png', img_cv)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        # 创建响应对象，将pos和img_b64传输给前端,pos是一个列表，每个元素是一个字典，包含了每题的开始位置和结束位置
        response = make_response(json.dumps({'img':img_b64,'pos':pos}, default=str))
        response.headers['Content-Type'] = 'text/plain'
        return(response)

@job_manage.route("/publish_work/",methods=["POST","GET"])
@login_required 
@permission_required(Permission.job_publish)
def publish_work():
    db.session.commit()
    if request.method=="POST":
        title=request.form.get("title")
        if job.query.filter_by(job_name=title).first():
            return("作业名重复")
        #获取后台传来的structrued数据
        structrued1=request.form.get("structrued")
        structrued=json.loads(structrued1)                
        answer=request.form.get("answers")
        answer=json.loads(answer)
        classlist=request.form.get("classlist")
        classlist=json.loads(classlist)
        g=request.form.get("grade") 
        g=json.loads(g)       
        tags=request.form.get("tags")
        tags=json.loads(tags)
        files=request.files.get("file")
        subject=current_user.teacher.subject
        total=0
        select=[]
        no_Select={}
        s_answer={}
        for key in structrued.keys():
            if "选" in structrued[key]["类型"]:
                s={}
                total+=structrued[key]["分值"]*structrued[key]["小题数"]
                s["大题号"]=key
                s["初始题号"]=structrued[key]["初始题号"]
                s["题目数量"]=structrued[key]["小题数"]
                s["分值"]=structrued[key]["分值"]
                s["位置"]=structrued[key]["位置"]
                select.append(s)
                for k in range(len(answer[key])):
                    s_answer[s["初始题号"]+k]=answer[key][k]
            else:
                total+=sum(structrued[key]["分值"].values())                
                for k in structrued[key]["位置"].keys():
                    NS={}                    
                    NS["位置"]=structrued[key]["位置"][k]
                    NS["分值"]=structrued[key]["分值"][k]
                    no_Select[k]=NS
        if files:
            filename=secure_filename(files.filename)
            filename=title+"."+filename.split(".")[-1]
            url=os.path.join(os.getcwd(),"app/static/job/paper/question_paper",subject)
            if not os.path.exists(url):
                os.makedirs(url)
            url=os.path.join(url,filename)
            files.save(url)
        job1=job(job_name=title,answerCardStructure=json.dumps(structrued),select_answer=json.dumps(s_answer),context=json.dumps(tags),subject=subject,publisher=current_user.id ,multiple_choice_infor=json.dumps(select),no_multiple_choice_infor=json.dumps(no_Select),total1=total,question_paper=filename,publish_time=datetime.datetime.now())
        db.session.add(job1)
        db.session.flush()
        job1.paper_url=str(job1.id)+".png"
        db.session.commit()
        path=os.path.join(os.getcwd(),"app","static","job","answer",str(job1.id))  
        path1=os.path.join(os.getcwd(),"app","static","job","job_readed",str(job1.id))      
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path1):
            os.makedirs(path1)        
        if g:
            class_list=db.session.query(class_info).join(grade_info).filter(grade_info.id.in_(g)).filter(class_info.attribute=="行政班").all()    
        else:          
            class_list=db.session.query(class_info).filter(class_info.id.in_(json.loads(request.form.get("classlist")))).all()
        #将答题卡移至对应的文件夹中
        path=os.path.join(os.getcwd(),"app","static","job","answerCard",subject)
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            path1=os.path.join(os.getcwd(),"app","static","job","temp",str(current_user.id)+".png")
            path2=os.path.join(os.getcwd(),"app","static","job","answerCard",str(job1.id)+".png")
            #给答题卡添加二维码
            img = Image.open(path1)
            n=img.width//82
            messeage=str(job1.id)+"_"+str(current_user.realname)+"_"+str(job1.job_name)
            creat_paper.qr_paste(messeage,img,(n*68,n*20),n*12) 
            img.save(path2)
            img.save(path1)
        except Exception as e:            
            db.session.rollback()
        #将作业发布给对应的班级
        if class_list:  # 作业布置 
            for i in class_list:                    
                check_job=job_class.query.join(job,job_class.job).filter(job.job_name==title,job_class.class_id==i.id,job.subject==current_user.teacher.subject).first()  #避免重复布置相同作业
                if check_job:
                    messege="%s班已经有名为《%s》的作业！" %(check_job.class_info.class_name,title)
                    return(messege)
                else:
                    job_publish = job_class(class_id=i.id,job_id=job1.id)
                    db.session.add(job_publish)
                    db.session.flush()
                    for j in i.students:
                        j_stu=job_student(job_id=job1.id,student=j.number)
                        db.session.add(j_stu)
                        db.session.flush()
        else:
            messege="没有设置班级,请在作业主界面选择班级布置作业！"
            return(messege)
        db.session.commit()
        return("success")
 
@job_manage.route("/super_judge/",methods=["POST","GET"]) #识别二维码阅卷
@login_required 
@permission_required(Permission.job_submit)
def super_judge():
    path=os.path.join(os.getcwd(),"app","static","job","answer","all",str(current_user.id))
    #遍历path文件夹下的所有文件
    files=os.listdir(path)
    n=0
    id=[]
    m=0
    #如果path文件夹下没有文件，则返回
    if not files:
        return("没有作业需要阅卷")
    for i in files:
        #获取文件的绝对路径
        file=os.path.join(path,i)
        #判断是否是文件夹
        if not os.path.isdir(file):
            standard=judge.open_answer_card(os.path.join(os.getcwd(),"app","static","job","paper","standard.png"))
            img=judge.open_student_card(file)
            img=judge.paper_ajust(standard,img) 
            qr_img=img[judge.n*20:judge.n*35,judge.n*68:judge.n*80]
            #形态学操作，去除噪点，补上缺点
            qr_img=cv2.morphologyEx(qr_img, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
            qr_img=cv2.morphologyEx(qr_img, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
            _, qr_img = cv2.threshold(qr_img, 180, 255, cv2.THRESH_BINARY)
            
            messeage=judge.qr_recognize(qr_img,(0,qr_img.shape[0],0,qr_img.shape[1]))
            if messeage:
                print(messeage)
            else:
                m+=1
                print("没有识别到二维码")
            number=judge.number_pos(img)
            if messeage and number:     
                messeage=messeage[0].split("_")                
                job_id=messeage[0]
                if job_id not in id:
                    id.append(job_id)
                msg=check_student_number(number,job_id)
                if msg !="success":
                    #将异常卷的信息存入abnormal_job表中
                    ab=abnormal_job(job_id=int(job_id),paper=i,student_id=number,reason=msg,time=datetime.datetime.now(),teacher_id=current_user.teacher.id)
                    db.session.add(ab)
                    db.session.flush()
                    #将异常卷移至abnormal_paper文件夹中
                    path1=os.path.join(os.getcwd(),"app","static","job","abnormal_paper",str(job_id))
                    if not os.path.exists(path1):
                        os.makedirs(path1)
                    os.rename(file,os.path.join(path1,i))
                    continue
                msg1,mark=multiple_choice_judge(img,job_id)
                if msg1!="success":
                    ab=abnormal_job(job_id=job_id,paper=i,student_id=number,reason=mark,time=datetime.datetime.now(),teacher_id=current_user.teacher.id)
                    db.session.add(ab)
                    db.session.flush()
                    #将异常卷移至abnormal_paper文件夹中
                    path1=os.path.join(os.getcwd(),"app","static","job","abnormal_paper",str(job_id))
                    if not os.path.exists(path1):
                        os.makedirs(path1)
                    os.rename(file,os.path.join(path1,i))
                    db.session.commit()
                    if msg1=="作业不存在": 
                        continue
                se=update_select_info(number,job_id,mark)
                j_stu=job_student.query.filter(job_student.job_id==int(job_id),job_student.student==number).first()
                j_stu.select_mark=se
                j_stu.submit_time=datetime.datetime.now()
                n+=1
                #将已经阅卷的卷子移至job_readed文件夹中,并修改文件名
                if msg=="success" and msg1=="success":  
                    path1=os.path.join(os.getcwd(),"app","static","job","job_readed",str(job_id))
                    if not os.path.exists(path1):
                        os.makedirs(path1)
                    path2=os.path.join(path1,str(number)+".png")
                    os.rename(file,path2)
                #生成非选择题阅卷信息
                non_multiple_choice_to_read(number,job_id)
    for i in id:
        update_class_info(i)
    db.session.commit()
    return(jsonify("%s份作业未成功识别二维码，成功阅卷%s份" %(m,n)))

@job_manage.route("/UpdateClassInfo/",methods=["POST","GET"])
@login_required 
@permission_required(Permission.job_submit)
def UpdateClassInfo():
    if request.method=="POST":
        id=request.get_json()["id"]
        update_class_info(id)
        return(jsonify("成功更新成绩信息"))

@job_manage.route("/getCard/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def getCard():
    if request.method=="POST":
        url=request.form.get("url")
        url=os.path.join(os.getcwd(),"app","static","job",url)
        print(url)
        img_b64=get_img(url)
        response = make_response(img_b64)
        # 设置响应头
        response.headers['Content-Type'] = 'img/png'
        return(response)

@job_manage.route("/modifyAnswer/",methods=["POST","GET"])
@login_required
@permission_required(Permission.job_publish)
def modifyAnswer():
    if request.method=="POST":
        data=request.get_json()        
        id=data["id"]
        answer=data["answer"]
        job_=job.query.filter(job.id==id).first()
        answer_=json.loads(job_.select_answer)
        for key in answer.keys():
            answer_[key]=answer[key]
        job_.select_answer=json.dumps(answer_)
        db.session.commit()
        return(jsonify("成功更新答案"))

def multiple_choice_judge(answer_card,job_id):
    msg=""
    mark={}
    job_=db.session.query(job).filter(job.id==job_id).first()
    if job_:       
        structrued=json.loads(job_.answerCardStructure)
        multiple_choice_infor=json.loads(job_.multiple_choice_infor)
        answer=json.loads(job_.select_answer)
        tag=json.loads(job_.context)
        for q in multiple_choice_infor:
            #切出题目区域垂直方向为start到end，水平方向为n*7到n*75
            img=answer_card[q['位置']['start']*judge.n:q['位置']['end']*judge.n,judge.n*7:judge.n*75]
            initial_number=q['初始题号']
            score=q['分值']
            quantity=q['题目数量']
            student_answer=judge.check_select(img,quantity)
            for k in student_answer.keys():
                if student_answer[k]==answer[str(initial_number+k-1)]:

                    mark[initial_number+k-1]=[student_answer[k],score,tag[initial_number+k-2]]
                   
                else:
                    mark[initial_number+k-1]=[student_answer[k],0,tag[initial_number+k-2]]
    
        msg="success"
    else:
        msg="作业不存在"
    return(msg,mark)

def check_student_number(number,id):
    if  len(number)!=10:
        return("学号长度不正确")
    job_=job.query.filter(job.id==int(id)).first()
    j_stu=job_student.query.filter(job_student.job_id==int(id),job_student.student==number).first()
    if not j_stu: #判断该生是否有作业任务，若无，不作阅卷处理
        return("学号为%s的学生没有id为%s作业任务" %(number,id))
    else:#判断该生是否已经阅卷，若已阅卷，不作阅卷处理
        if j_stu.mark:
            return("%s已阅卷,请检查是否重复阅卷" %number)
        else:
            return("success")

#更新选择题答案信息
def update_select_info(number,job_id,answer):
    se=0    
    for key in answer.keys():
        jt=job_detail.query.filter(job_detail.student==number,job_detail.job_id==job_id,job_detail.serial_No==key).first()
        if jt:    
            jt.answer=answer[key][0]
            jt.mark=answer[key][1]
            jt.tag=answer[key][2]
        else:
            jt=job_detail(job_id=job_id,student=number,serial_No=key,answer=answer[key][0],mark=answer[key][1],tag=answer[key][2])
            db.session.add(jt)
        db.session.flush()
        se+=answer[key][1]
    job_student_=job_student.query.filter(job_student.job_id==job_id,job_student.student==number).first()
    job_student_.select_mark=se
    db.session.commit()
    return(se)

#更新班级成绩统计信息
def update_class_info(id):
    j_cla=job_class.query.filter(job_class.job_id==int(id)).all()  #阅卷完成后统计作业情况，查询被布置了此作业的所有班级
    #分别统计每个班的作业情况，包括提交人数，平均分，最高分，最低分，标准差
    for j in j_cla:
        #job_student有外键student连接到student表，class_student表有外键class_id连接到class_info表,student_id连接到student表,运用join连接查询，获取每个班级的学生作业情况
        # 如果值为空，则设置为0     
        average=db.session.query(func.avg(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #平均分
        submit_number=job_student.query.filter(job_student.job_id==int(id),job_student.mark!=None).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id).count() #提交人数
        max=db.session.query(func.max(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #最高分
        min=db.session.query(func.min(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #最低分
        std=db.session.query(func.stddev(job_student.mark)).join(student,job_student.student==student.number).join(class_student,student.id==class_student.student_id).filter(class_student.class_id==j.class_id,job_student.job_id==int(id)).scalar() #标准差
        if average:
            j.average=average
        if submit_number:
            j.submit_number=submit_number
        if max:
            j.max=max
        if min:
            j.min=min
        if std:
            j.std=std
        db.session.flush()
    db.session.commit()
    return("success")

def non_multiple_choice_to_read(number,id):
    job_=job.query.filter(job.id==int(id)).first()
    complete=json.loads(job_.no_multiple_choice_infor)
    #遍历complete字典生成填空题阅卷信息
    for key in complete.keys():   
        jt=job_detail.query.filter(job_detail.student==number,job_detail.job_id==int(id),job_detail.serial_No==key).first()
        if not jt:
            jt=job_detail(job_id=int(id),student=number,serial_No=key,answer='F',tag=json.loads(job_.context)[int(key)-1])
            db.session.add(jt)
            db.session.flush()

def get_img(url):#打开图片并转换为base64格式
    img=Image.open(url)
    img_cv=np.array(img)
    img_cv=cv2.cvtColor(img_cv,cv2.COLOR_RGB2BGR)
    retval, buffer = cv2.imencode('.png', img_cv)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    return(img_b64)