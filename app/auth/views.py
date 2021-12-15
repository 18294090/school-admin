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
