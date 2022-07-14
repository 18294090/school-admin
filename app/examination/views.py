from flask import render_template, redirect, flash, request
from ..models import grade_info, class_info, teacher, user, test,test_scores
from .. import db
from .forms import publish
from . import examination
from flask_login import login_required, current_user
import time


@examination.route("/",methods=["POST","GET"])
def main():
    if current_user.role.role=="admin":
        t=test.query.all()
        class_=class_info.query.all()
        subjects=["语文","数学","外语","政治","历史","地理","物理","化学","生物","通用技术","信息技术"]
    elif current_user.role.role=="teacher":
        t=test.query.filter(test.teacher_id==current_user.teacher.id).all()
        class_=current_user.teacher.teacher_imformation.class_info
        subjects=[current_user.teacher.teacher_imformation.subject]
    elif current_user.role.role=="student":
        return("student")
    if request.method=="POST":
        test_name=request.form["test_name"]
        classes=request.form.getlist("class_name")
        for i in subjects:
            for j in classes:
                test_=test(test_name=test_name,class_id=j,subject=i,publisher=current_user.id,publish_time=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
                db.session.add(test_)
                db.session.commit()    
    return(render_template("examination/mainpage.html", t=t,class_=class_))

