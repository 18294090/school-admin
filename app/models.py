"""数据库模型文件，在这里定义数据库模型，一个模型对应一张数据表"""
from sqlalchemy.orm import backref
from app import db
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return (user.query.get(int(user_id)))

class role(db.Model):  # 角色表
    __table_args__ = {'extend_existing': True}
    __tablename__ = "role"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    role = db.Column(db.String(16), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
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
    enrollment = 1  # 入学
    class_grouping = 2  # 分班
    offer_courses = 4  # 课程开设
    assign_teachers = 8  # 任课教师分配
    job_republish = 16  # 作业发布
    job_submission = 32  # 作业提交
    job_evaluation = 64  # 作业评价


class user(UserMixin, db.Model):  # 用户表
    __table_args__ = {'extend_existing': True}
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    realname = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, ForeignKey("role.id"))
    role = db.relationship("role",backref=db.backref("user", lazy="dynamic"))
    phone_number = db.Column(db.String(11))
    id_number = db.Column(db.String(18), unique=True)
    gender = db.Column(db.String(1))
    login_time = db.Column(db.DateTime)
    status = db.Column(db.String(64))
    teacher = db.relationship('teacher',backref=db.backref("user"))
    
    # 禁止读密码
    @property
    def password(self):
        return ("密码字段不可读")  # 当调用密码字段时，返回错误信息

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return(check_password_hash(self.password_hash, password))

class grade_info(db.Model):  # 年级信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "grade_info"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    grade_name = db.Column(db.String(64))
    grade_master = db.Column(db.Integer, ForeignKey("user.id"))
    academic_year =db.Column(db.Date)

class class_info(db.Model):  # 班级信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "class_info"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    class_name = db.Column(db.String(64), unique=True)
    grade_id = db.Column(db.Integer, ForeignKey("grade_info.id"))
    grade = db.relationship('grade_info',backref=db.backref("class_info", uselist=False))
    class_master = db.Column(db.Integer, ForeignKey("user.id"))
    attribute = db.Column(db.String(64))
    student = db.relationship('student',backref=db.backref("class_info", uselist=False))
    teacher =  db.relationship('user',backref=db.backref("class_info"))
    teaching_information =db.relationship('teaching_information',backref=db.backref("class_info"))
    
class teacher(db.Model):  # 教师信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "teacher"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("user.id"))
    subject = db.Column(db.String(64))
    teaching_information = db.relationship('teaching_information',backref=db.backref("teacher"))

class teaching_information(db.Model):  # 教师任教信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "teaching_information"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    subject = db.Column(db.String(64))
    teacher_id = db.Column(db.Integer, ForeignKey("teacher.id"))
    class_id = db.Column(db.Integer, ForeignKey("class_info.id"))

class job(db.Model):  # 作业
    __table_args__ = {'extend_existing': True}
    __tablename__ = "job"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    job_name = db.Column(db.String(64))
    class_id = db.Column(db.Integer, ForeignKey("class_info.id"))
    class_name = db.relationship("class_info", backref=db.backref('jobs', lazy='dynamic'))
    publish_time = db.Column(db.DateTime)
    publisher = db.Column(db.Integer, ForeignKey("user.id"))
    deadline = db.Column(db.DateTime)

class job_submission(db.Model):  #作业提交信息
    __table_args__ = {'extend_existing': True}
    __tablename__ = "job_submission"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    job_id = db.Column(db.Integer, ForeignKey("job.id"))
    student = db.Column(db.Integer, ForeignKey("student.id"))
    job_assessment = db.Column(db.Integer)
    submit_time = db.Column(db.DateTime)

class job_assessment:
    A=5
    B=4
    C=3
    D=2
    E=1
    F=0

class test(db.Model):  # 考试
    __table_args__ = {'extend_existing': True}
    __tablename__ = "test"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    exam_name = db.Column(db.String(64))
    class_id = db.Column(db.Integer, ForeignKey("class_info.id"))
    class_name = db.relationship("class_info", backref=db.backref('class_info', lazy='dynamic'))
    publish_time = db.Column(db.DateTime)
    publisher = db.Column(db.Integer, ForeignKey("user.id"))

class test_scores(db.Model):  # 考试成绩
    __table_args__ = {'extend_existing': True}
    __tablename__ = "test_scores"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    exma_id = db.Column(db.Integer, ForeignKey("test.id"))
    scores = db.Column(db.Integer)
    student = db.Column(db.Integer, ForeignKey("student.id"))
    submit_time = db.Column(db.DateTime)
    
class student(db.Model):  # 学生
    __table_args__ = {'extend_existing': True}
    __tablename__ = "student"
    id= db.Column(db.Integer, autoincrement=True, primary_key=True)
    number = db.Column(db.String(64),ForeignKey("user.username"))
    user_infor = db.relationship("user",backref=db.backref("student"))
    name = db.Column(db.String(64))
    class_id = db.Column(db.Integer, ForeignKey(class_info.id))

class assessment(db.Model):  # 教师对学生的评价
    __table_args__ = {'extend_existing': True}
    __tablename__ = "assessment"
    id= db.Column(db.Integer, autoincrement=True, primary_key=True)
    student = db.Column(db.Integer, ForeignKey("student.id"))
    teacher = db.Column(db.Integer, ForeignKey("teacher.id"))
    time = db.Column(db.DateTime)
    content = db.Column(db.Text)




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