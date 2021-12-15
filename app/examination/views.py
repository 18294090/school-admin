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

