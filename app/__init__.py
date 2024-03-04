"""主程序工厂函数定义，数据库对象定义"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_datepicker import datepicker
import os
import json
from flask_migrate import Migrate
from flask_socketio import SocketIO

login_manager = LoginManager()  # flask-login模块进行登录管理
login_manager.login_view = "auth.login"
ckeditor = CKEditor()  # 富文本编辑器插件
bootstrap = Bootstrap5()
db = SQLAlchemy()
csrf = CSRFProtect()  # 跨站攻击保护
def from_json(value):
    return json.loads(value)


def create_app(config_name):
    app = Flask(__name__)  # app初始化
    app.config.from_object(config[config_name])  # 先导入设置
    config[config_name].init_app(app)
    db.init_app(app)  # 初始化sqlalchemy，必须先导入设置，然后初始化数据库，否则要报错
    bootstrap.init_app(app) 
    socketio = SocketIO(app)
    @app.teardown_request #请求结束后关闭数据库连接，如果检测到错误，则回滚
    def teardown_request(exception): #
        if exception:
            print("数据库错误回滚")
            db.session.rollback()            
        db.session.remove()   
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    app.config['UPLOAD_FOLDER'] = os.getcwd()+"\\app\\static\\"
    app.config['MAX_CONTENT_LENGTH'] = 32 * 4000 * 3000 #文件大小限制
    app.config['SQLALCHEMY_POOL_SIZE'] = 20 #数据库连接池大小
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 5 #数据库连接超时时间
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600 #数据库连接回收时间
    ckeditor.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    datepicker(app)
    app.jinja_env.filters["from_json"]=from_json
    from .main import main
    from .auth import auth as auth_blueprint
    from .job import job_manage
    from .examination import examination
    from .manage import manage
    from .pedagogical_analysis import pedagogical_analysis
    migrate = Migrate(app, db)
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(job_manage,url_prefix="/job")
    app.register_blueprint(examination,url_prefix="/exam")
    app.register_blueprint(manage,url_prefix="/manage")
    app.register_blueprint(pedagogical_analysis,url_prefix='/p_analysis')
    socketio.run(app, debug=True)
    return(app)
