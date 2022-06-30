"""网页视图上窗体的定义"""
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import PasswordField, SubmitField, SelectField, StringField, IntegerField, DateField
from flask_wtf import FlaskForm
from flask_wtf.file import DataRequired
from flask_ckeditor import CKEditorField
from flask_codemirror.fields import CodeMirrorField
from wtforms.validators import InputRequired, EqualTo

class publish(FlaskForm):
    subject = StringField(label="学科", validators=[DataRequired('确定学科')])
    job_name = StringField(label="作业名称", validators=[DataRequired('作业名称')])
