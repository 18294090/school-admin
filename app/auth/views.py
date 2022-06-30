<<<<<<< HEAD
from flask import render_template, redirect, request, url_for, flash
from . import auth
from flask_login import login_user,logout_user,login_required
from ..models import user
from .forms import userlogin
from .. import db
import time
from flask_login import current_user


@auth.route("/", methods=["POST", "GET"])
def login():
    form1 = userlogin()
    if form1.validate_on_submit():
        u = user.query.filter_by(username=form1.username.data).first()
        
        if (u and u.verify_password(form1.password.data))  :
            login_user(u, form1.remember_me.data)
            next = request.args.get('next')
            if not next or not next.startswith("/"):
                next = url_for('main.index')
                u.login_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                db.session.commit()
            return(redirect(next))        
        return("错误的账号或密码")
    return(render_template("auth/login.html", form1=form1))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("你已成功退出系统")
    return(redirect(url_for('auth.login')))

@auth.route("/reset/<id>")
@login_required
def reset(id):
    if current_user.id == int(id) or current_user.role == "admin":
        u=user.query.filter(user.id==id).first()
        u.password="123456"
        db.session.flush()
        db.session.commit()
        return(redirect(url_for('auth.login')))
    else:
        return("你没有权限")

@auth.route("/ad")
def ad():
    admin=user(username="admin",role_id=3,password="123")
    print(admin)
    db.session.add(admin)
    db.session.commit()
    return("初始化")

@auth.route("/register", methods=["POST", "GET"])
def reg():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("Password1")
        id_number = request.form.get("id_number")
        phone_number = request.form.get("phone_number")        
        u=user.query.filter_by(id_number=id_number).first()
        print(username,password,id_number,phone_number)
        if u and not u.username:
            u.username=username
            u.password=password
            u.phone_number=phone_number
            db.session.commit()
            return(redirect(url_for('auth.login')))
        else:
            return("注册失败，请联系管理员")
    return(render_template("auth/reg.html"))

@auth.route("/personal_details")
def personal_details():
    return(render_template('auth/personal_details.html'))

=======
from flask import render_template, redirect, request, url_for, flash
from . import auth
from flask_login import login_user,logout_user,login_required
from ..models import user
from .forms import userlogin
from .. import db
import time


@auth.route("/", methods=["POST", "GET"])
def login():
    form1 = userlogin()
    if form1.validate_on_submit():
        u = user.query.filter_by(username=form1.username.data).first()
        id_number =  user.query.filter_by(id_number=form1.username.data).first()
        if (u and u.verify_password(form1.password.data))  :
            login_user(u, form1.remember_me.data)
            next = request.args.get('next')
            if not next or not next.startswith("/"):
                next = url_for('main.index')
                u.login_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                db.session.commit()
            return(redirect(next))
        if id_number and id_number.verify_password(form1.password.data):
            login_user(id_number, form1.remember_me.data)
            next = request.args.get('next')
            if not next or not next.startswith("/"):
                next = url_for('main.index')
                id_number.login_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
                db.session.commit()
            return(redirect(next))
        flash("错误的账号或密码")
    return(render_template("auth/login.html", form1=form1))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("你已成功退出系统")
    return(redirect(url_for('auth.login')))

@auth.route("/reset/<id>")
def reset(id):
    u=user.query.filter(user.id==id).first()
    u.password="123456"
    db.session.flush()
    db.session.commit()
    return("重置成功")
>>>>>>> d989a01c055dd7066c1fb6cabda1c43d81584f09
