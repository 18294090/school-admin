<<<<<<< HEAD
from flask import render_template, redirect, flash, request
from ..models import grade_info, class_info, teacher, user, test,test_scores
from .. import db
from .forms import publish
from . import examination
from flask_login import login_required, current_user


@examination.route("/",methods=["POST","GET"])
def main():
    if current_user.role.role=="admin":
        t=test.query.all()
        class_=class_info.query.all()
    elif current_user.role.role=="teacher":
        t=test.query.filter(test.teacher_id==current_user.teacher.id).all()
        class_=current_user.teacher.teacher_imformation.class_info
    elif current_user.role.role=="student":
        return("student")
    
    return(render_template("examination/mainpage.html", t=t,class_=class_))

=======
from flask import render_template, redirect, flash, request
from ..models import grade_info, class_info, teacher, user, job
from .. import db
from .forms import publish
from . import examination


@examination.route("/",methods=["POST","GET"])
def job():
    p = publish()
    subject = request.form.get('subject')
    job_name = request.form.get('job_name')
    deadline = request.form.get('date')
    
    return(render_template("job/mainpage.html", p=p,d=deadline))

>>>>>>> d989a01c055dd7066c1fb6cabda1c43d81584f09
