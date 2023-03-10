"""网页视图上窗体的定义"""
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import PasswordField, SubmitField, SelectField, StringField, IntegerField, DateField
from flask_wtf import FlaskForm
from flask_wtf.file import DataRequired
from flask_ckeditor import CKEditorField
from flask_codemirror.fields import CodeMirrorField
from wtforms.validators import InputRequired, EqualTo
subjects =[(1, '语文'), (2, '数学'), (3, '外语'), (4, '政治'), (5, '历史'),(6, '地理'), (7, '物理'), (8, '化学'), (9, '生物'), (9, '信息技术'), (10, '通用技术'), (11, '音乐'), (12, '体育'), (13, '美术'), (14, '科学')]


