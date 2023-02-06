"""登录页面视图上窗体的定义"""
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import PasswordField, SubmitField, SelectField, StringField, IntegerField, BooleanField
from flask_wtf import FlaskForm
from flask_wtf.file import DataRequired
from flask_ckeditor import CKEditorField
from flask_codemirror.fields import CodeMirrorField
from wtforms.validators import InputRequired, EqualTo


class loginform(FlaskForm):
    class_name = SelectField(label="请选择班级", validators=[DataRequired('请选择标签')],
        render_kw={'class': 'form-control'},
        default=3,

        )
    stuname = SelectField(label="请选择学生名", validators=[DataRequired('请选择标签')],
        render_kw={'class': 'form-control'},
        default=3,
        )
    password = PasswordField("请输入密码", validators=[InputRequired("请输入密码")])
    submit = SubmitField("登录")


class userlogin(FlaskForm):
    username = StringField(label="用户名", validators=[DataRequired('请输入账号')])
    password = PasswordField("密码", validators=[InputRequired("请输入密码")])
    remember_me = BooleanField("保持登录状态")
    submit = SubmitField("登录")
