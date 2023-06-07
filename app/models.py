"""数据库模型文件，在这里定义数据库模型，一个模型对应一张数据表"""
from sqlalchemy.orm import backref
from app import db
from sqlalchemy import ForeignKey,func,CheckConstraint,case,event
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from . import login_manager
from datetime import datetime
import json


@login_manager.user_loader
def load_user(user_id):
    return (user.query.get(int(user_id)))

class role(db.Model):  # 角色表
    __table_args__ = {'extend_existing': True}
    __tablename__ = "role"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    role = db.Column(db.String(16), unique=True)    
    
    permissions = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permission(self):
        self.permissions = 0

    def has_permission(self, perm):
        return(self.permissions & perm == perm)
class Permission:
    job_publish= 1 # 任教班级学习任务的发布
    job_grade=2 # 全年级学习任务发布
    job_submit = 4 # 作业提交
    admin = 8 # 管理权限

class user(UserMixin, db.Model):  # 用户表
    __table_args__ = {'extend_existing': True}
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    realname = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, ForeignKey("role.id"))
    role = db.relationship("role", backref=db.backref("users", lazy="dynamic"), uselist=False, lazy="joined")
    phone_number = db.Column(db.String(11))
    id_number = db.Column(db.String(18), unique=True)
    gender = db.Column(db.String(1))
    login_time = db.Column(db.DateTime)
    status = db.Column(db.String(64))
    job = db.relationship("job", order_by = "job.publish_time.desc()",backref=db.backref("user"))  #order_by用于排序，desc（）为降序
    # 禁止读密码
    @property
    def password(self):
        return ("密码字段不可读")  # 当调用密码字段时，返回错误信息
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    def verify_password(self, password):
        return(check_password_hash(self.password_hash, password))
    def can(self,perm):
        return self.role is not None and self.role.has_permission(perm)
    def is_administrator(self):
        return(self.can(Permission.admin))
class AnonymousUser(AnonymousUserMixin):
    def can(self,permission):
        return False
    def is_administrator(self):
        return False
login_manager.anonymous_user=AnonymousUser

class grade_info(db.Model):  # 年级信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "grade_info"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    grade_name = db.Column(db.String(64), unique=True)
    grade_master = db.Column(db.Integer, ForeignKey("user.id"))
    academic_year =db.Column(db.Integer)
    __table_args__ = (
        CheckConstraint('year >= 1900 AND year <= 2100', name='check_year'),)
    
class class_info(db.Model):
    __tablename__ = "class_info"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    class_name = db.Column(db.String(64), unique=True)
    grade_id = db.Column(db.Integer, db.ForeignKey("grade_info.id"))
    grade = db.relationship('grade_info', backref=db.backref("classes"))
    class_master = db.Column(db.Integer, db.ForeignKey("teacher.id"))
    teacher =db.relationship("teacher",backref=db.backref("class_info"))
    attribute = db.Column(db.String(64))
    students = db.relationship('student', secondary='class_student', back_populates='classes')

class student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    number = db.Column(db.String(64), index=True)
    name = db.Column(db.String(64))
    gender = db.Column(db.String(1))
    classes = db.relationship('class_info', secondary='class_student', back_populates='students')
    @property
    def password(self):
        return ("密码字段不可读")  # 当调用密码字段时，返回错误信息

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return(check_password_hash(self.password_hash, password))

class class_student(db.Model):
    __tablename__ = "class_student"
    class_id = db.Column(db.Integer, db.ForeignKey("class_info.id", ondelete='CASCADE'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id", ondelete='CASCADE'), primary_key=True)
    classes = db.relationship('class_info', backref=db.backref("class_student"))
    students = db.relationship('student', backref=db.backref("class_student"))

class teacher(db.Model):  # 教师信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "teacher"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    subject = db.Column(db.String(64))
    user_info = db.relationship('user',backref=db.backref("teacher",uselist=False))
    representative = db.relationship('representative',backref=db.backref("teacher"))

class teaching_information(db.Model):  # 教师任教信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "teaching_information"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    subject = db.Column(db.String(64))
    teacher_id = db.Column(db.Integer, ForeignKey("teacher.id"))
    teacher = db.relationship('teacher',backref=db.backref("teaching_information", lazy="dynamic"))
    class_id = db.Column(db.Integer, ForeignKey("class_info.id"))
    class_info = db.relationship('class_info',backref=db.backref("teaching_information"))

class job(db.Model):  # 作业
    __table_args__ = {'extend_existing': True}
    __tablename__ = "job"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    job_name = db.Column(db.String(64))
    publish_time = db.Column(db.DateTime)
    publisher = db.Column(db.Integer, ForeignKey("user.id",))
    question_paper = db.Column(db.String(64))
    subject = db.Column(db.String(64))    
    context = db.Column(db.Text)
    select =db.Column(db.Integer) #选择题数量
    s_m=db.Column(db.Integer)#选择题分数
    select_answer=db.Column(db.Text)
    complete = db.Column(db.String(64))#为一个列表，为各题的分数，如：[6,6,8]表示填空题有三题，分别为6分6分8分
    paper_url = db.Column(db.String(64))
    line = db.Column(db.String(64))    
    #total字段为作业总分，值为select字段乘以s_m字段的和加上complete字段的和，total字段的值在作业发布时自动计算，不需要手动输入

        
    @property
    def total(self):
        # Calculate the total score based on select, s_m, and complete fields
        select_score = self.select * self.s_m
        complete_score = sum(json.loads(self.complete))
        return select_score + complete_score
    #作业和班级的关系，一个作业可以有多个班级，一个班级可以有多个作业，删除作业时，job_class表中的数据也会被删除，而删除job_class表中的数据时，不会影响作业表
    job_class = db.relationship("job_class",  back_populates="job",cascade="all, delete")
    job_detail = db.relationship("job_detail",  back_populates="job",cascade="all, delete")
    job_student = db.relationship("job_student",  back_populates="job",cascade="all, delete")

#数据表abnormal_job用于存储阅卷中的异常卷，如考号未正确识别，或者考号重复，或选择题多选，漏选，或者填空题多填，少填，选择题题目数量与作业不符，填空题题目数量与作业不符等    
class abnormal_job(db.Model):
    __tablename__ = "abnormal_job"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    job_id = db.Column(db.Integer, ForeignKey("job.id", ondelete='CASCADE'),nullable=False)
    job = db.relationship("job", backref=db.backref("abnormal_job", lazy="dynamic"))
    reason = db.Column(db.String(64))
    paper = db.Column(db.String(64))
    student_id = db.Column(db.String(20),nullable=True)

class job_class(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "job_class"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    class_id = db.Column(db.Integer, ForeignKey("class_info.id", ondelete='CASCADE'),nullable=False)
    class_info =db.relationship("class_info", foreign_keys=[class_id], backref=db.backref('job_class',lazy="dynamic", cascade="all, delete"))
    #job_id为指向job表的外键，删除job_class表中的数据时，不会影响作业表
    job_id = db.Column(db.Integer, ForeignKey("job.id", ondelete='CASCADE'),nullable=False)
    job = db.relationship("job", order_by="job.publish_time.desc()",back_populates="job_class")
    average=db.Column(db.Float(precision=2),default=0)
    max=db.Column(db.Float(precision=2),default=0)
    min=db.Column(db.Float(precision=2),default=0)
    submit_number=db.Column(db.Integer,default=0)
    std=db.Column(db.Float(precision=2),default=0)
    date=db.Column(db.DateTime,default=datetime.now)


class job_detail(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "job_detail"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    job_id = db.Column(db.Integer, ForeignKey("job.id", ondelete='CASCADE'),nullable=False)
    job = db.relationship("job", back_populates="job_detail")
    student = db.Column(db.String(64), ForeignKey("student.number", ondelete='CASCADE'),nullable=False)
    stu =db.relationship("student", backref=db.backref("job_detail", lazy="dynamic", cascade="all, delete"), uselist=False)
    serial_No=db.Column(db.Integer) 
    answer=db.Column(db.String(64))
    tag=db.Column(db.String(64))
    mark=db.Column(db.Float(precision=2))

class job_student(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "job_student"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    job_id = db.Column(db.Integer, ForeignKey("job.id", ondelete='CASCADE'),nullable=False)
    job = db.relationship("job", order_by="job.publish_time.desc()",back_populates="job_student")    
    student = db.Column(db.String(64), ForeignKey("student.number", ondelete='CASCADE'),nullable=False)
    stu_ = db.relationship("student", backref=db.backref('job_student', lazy="dynamic", cascade="all, delete"), uselist=False)
    submit_time=db.Column(db.DateTime)
    select_mark=db.Column(db.Float(precision=2))
    complete_mark=db.Column(db.Float(precision=2))
    @hybrid_property
    def mark (self):
        if self.select_mark == None and self.complete_mark == None:
           return None
        elif self.select_mark == None and self.complete_mark != None:
            return self.complete_mark
        elif self.select_mark != None and self.complete_mark == None:
            return self.select_mark
        else:
            return self.select_mark + self.complete_mark

    @mark.expression
    def mark (cls):
        return case (
            [
                ((cls.select_mark == None) & (cls.complete_mark == None), None),
                ((cls.select_mark == None) & (cls.complete_mark != None), cls.complete_mark),
                ((cls.select_mark != None) & (cls.complete_mark == None), cls.select_mark),
            ],
            else_=cls.select_mark + cls.complete_mark
        )


class difficult(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    difficult =  db.Column(db.String(32))
    context = db.Column(db.String(128))

class representative(db.Model):
     id = db.Column(db.Integer, autoincrement=True, primary_key=True)
     student_id = db.Column(db.Integer, ForeignKey("student.id"))
     teacher_id = db.Column(db.Integer, ForeignKey("teacher.id"))
     subject = db.Column(db.String(64))
     student=db.relationship("student",backref=db.backref("representative",lazy="dynamic"))

"""class assessment(db.Model):  # 教师对学生的评价
    __table_args__ = {'extend_existing': True}
    __tablename__ = "assessment"
    id= db.Column(db.Integer, autoincrement=True, primary_key=True)
    student = db.Column(db.Integer, ForeignKey("student.id"))
    teacher = db.Column(db.Integer, ForeignKey("teacher.id"))
    time = db.Column(db.DateTime)
    content = db.Column(db.Text)
    mark =db.Column(db.Integer)"""

class job_assessment:
    A=5
    B=4
    C=3
    D=2
    E=1
    F=0

"""class test(db.Model):  # 考试
    __table_args__ = {'extend_existing': True}
    __tablename__ = "test"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    test_name = db.Column(db.String(64))
    class_id = db.Column(db.Integer, ForeignKey("class_info.id"))
    class_name = db.relationship("class_info", backref=db.backref('test', lazy='dynamic'))
    subject=db.Column(db.String(64))
    teacher_id = db.Column(db.Integer, ForeignKey("teacher.id"))
    teacher = db.relationship("teacher", backref=db.backref('teacher', lazy='dynamic'))
    publish_time = db.Column(db.DateTime)
    publisher = db.Column(db.Integer, ForeignKey("user.id"))
    publisher_info = db.relationship("user", backref=db.backref('publisher', lazy='dynamic'))
class test_scores(db.Model):  # 考试成绩
    __table_args__ = {'extend_existing': True}
    __tablename__ = "test_scores"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    exma_id = db.Column(db.Integer, ForeignKey("test.id"))
    scores = db.Column(db.Integer)
    student = db.Column(db.Integer, ForeignKey("student.id"))
    submit_time = db.Column(db.DateTime)"""

subject={
    "语文" : "chinese",
    "数学" : "math",
    "外语":"foreign_laguage",
    "政治":"politcs",
    "历史":"history",
    "地理":"geography",
    "物理":"physics",
    "化学":"chemisty",
    "生物":"biology",
    "信息技术":"it",
    "通用技术":"ut",
    "班主任":"master_teacher"
}