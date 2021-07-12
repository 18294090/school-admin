"""主程序工厂函数定义，数据库对象定义"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_codemirror import CodeMirror
from flask_wtf import CSRFProtect

ckeditor = CKEditor()  # 富文本编辑器插件
bootstrap = Bootstrap()
db = SQLAlchemy()
codeMirror = CodeMirror()  # 代码编辑器差距
csrf = CSRFProtect()  # 跨站攻击保护


def create_app(config_name):
    app = Flask(__name__)  # app初始化
    app.config.from_object(config[config_name])  # 先导入设置
    config[config_name].init_app(app)
    db.init_app(app)  # 初始化sqlalchemy，必须先导入设置，然后初始化数据库，否则要报错
    bootstrap.init_app(app)
    ckeditor.init_app(app)
    codeMirror.init_app(app)
    csrf.init_app(app)
    from .main import main
    app.register_blueprint(main)
    return(app)
