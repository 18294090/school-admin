"""网页视图上窗体的定义"""
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import PasswordField, SubmitField, SelectField, StringField, IntegerField
from flask_wtf import FlaskForm
from flask_wtf.file import DataRequired
from flask_ckeditor import CKEditorField
from flask_codemirror.fields import CodeMirrorField
from wtforms.validators import InputRequired, EqualTo

subjects =[(1, '语文'), (2, '数学'), (3, '外语'), (4, '政治'), (5, '历史'),(6, '地理'), (7, '物理'), (8, '化学'), (9, '生物'), (9, '信息技术'), (10, '通用技术'), (11, '音乐'), (12, '体育'), (13, '美术'), (14, '科学')]

class select_loginform(FlaskForm):
    class_name = SelectField(label="请选择班级", validators=[DataRequired('请选择标签')], render_kw={'class': 'form-control'},
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
    submit = SubmitField("登录")


class school_settings(FlaskForm):
    school = SelectField(label="请选择学段：",validators=[DataRequired('请选择标签')], render_kw={
            'class': 'form-control'
        },
        choices=[(1, '小学'), (2, '初中'), (3, '高中')],
        default=3,
        coerce=int)
    grade = IntegerField(label="请输入年级数")
    class_num = IntegerField(label="请输入每个年级的班级数")
    submit1 = SubmitField("确定")


class teacher_add(FlaskForm):
    username = StringField(label="姓名", validators=[DataRequired('请输入账号')])
    id_number = StringField(label="身份证号码", validators=[DataRequired('请输入身份证号码')])
    subject = SelectField(label="任教学科", validators=[DataRequired('请选择标签')], render_kw={
            'class': 'form-control'},
            choices=subjects,
            default=1,
            coerce=int)
    submit2 = SubmitField("确定")

class teacher_add_all(FlaskForm):
    file = FileField(label="请选择上传的文件", validators=[FileRequired('选择文件')])
    submit = SubmitField("提交")

class students_add(FlaskForm):
    file = FileField(label="请选择上传的文件", validators=[FileRequired('选择文件')])
    submit3 = SubmitField("提交")


