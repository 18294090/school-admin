from flask import render_template, redirect, flash, request
from ..models import grade_info, class_info, teacher, teaching_information, user, test,test_scores
from .. import db
from .forms import publish
from . import examination
from flask_login import login_required, current_user
import time


@examination.route("/",methods=["POST","GET"])
def main():
    c=[]
    if current_user.role.role=="admin":
        t=test.query.all()
        class_=class_info.query.all()
        
        for i in class_:
            if i.class_name not in c:
                c.append(i.class_name)
        subjects=["语文","数学","外语","政治","历史","地理","物理","化学","生物","通用技术","信息技术"]
    elif current_user.role.role=="teacher":
        t=current_user.teacher.teaching_information
        class_=current_user.teacher.teaching_information
        for i in class_:
            if i.class_info.class_name not in c:
                c.append(i.class_info.class_name)
        subjects=[current_user.teacher.subject]
    elif current_user.role.role=="student":
        return("student")
    if request.method=="POST":
        test_name=request.form["test_name"]
        classes=request.form.getlist("class_name")
        for i in subjects:
            for j in classes:
                print(i,j)
                test_=test(test_name=test_name,class_id=class_info.query.filter(class_info.class_name==j).first().id,subject=i,publisher=current_user.id,publish_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
                db.session.add(test_)
                db.session.commit()    
    return(render_template("examination/mainpage.html", t=t,class_=c))

