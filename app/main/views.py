"""视图文件，对请求进行处理，返回视图文件（网页模板）"""
 # -*-coding:utf-8-*-
import os
from flask.helpers import url_for
from sqlalchemy.sql.elements import Null
from .import main
from flask import render_template, redirect, flash, send_from_directory, request
from ..models import job,grade_info, class_info, representative, student, teacher, teaching_information, user,subject
from .forms import school_settings
from .. import db
from flask_login import current_user 


@main.route("/index", methods=["POST", "GET"])
def index():
    return(render_template("index.html"))


@main.route("/teaching", methods=["POST", "GET"])
def teaching():
    return(render_template("index.html"))


@main.route("/download/<path:filename>",methods=["POST","GET"])
def download(filename):
    dir = os.getcwd()
    dir =os.path.join(dir,"app/static/file/") 
    print(dir)   
    return send_from_directory(dir,filename, as_attachment=True)


@main.route("/search/<ob>", methods=["POST", "GET"])
def search(ob):
    return(str(ob))


@main.route("/test", methods=["POST", "GET"])
def test():
    
    return(render_template("test.html"))


@main.route("/")
def root():
    return(redirect("/auth/"))

@main.route('/answer/<path:path>')
def browse_static(path):
    id=path
    
    # get the absolute path of the static folder
    static_folder = os.path.join(os.getcwd(),'app','static')
    # get the absolute path of the requested file or folder
    abs_path = os.path.join(static_folder,'answer', path)
    
    path="answer/"+path
    # check if the path exists and it is a file
    if os.path.exists(abs_path) and os.path.isfile(abs_path):
        # send the file as a response
        
        
        return send_from_directory(static_folder, path)
    # check if the path exists and it is a folder
    elif os.path.exists(abs_path) and os.path.isdir(abs_path):
        # get the list of files and folders in the path
        files = os.listdir(abs_path)
        
        # render a template with the files and folders
        return render_template('folder.html', files=files, path=path,name=job.query.filter(job.id==id).first().job_name)
    else:
        # return 404 if the path does not exist or is not valid
        return "Not found", 404


