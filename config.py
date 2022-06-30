<<<<<<< HEAD
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'you will never know the key'
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = '18294090'
    MAIL_PASSWORD = 'zh64581948'
    FLASKY_MAIL_SUBJECT_PREFIX = '[FLASKY]'
    FLASKY_MAIL_SENDER = '*****'
    FLASKY_ADMIN = '*****'
    BOOTSTRAP_BOOTSWATCH_THEME = 'yeti'  # bootstrap主题设置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CKEDITOR_FILE_UPLOADER = 'main.upload'
    CKEDITOR_ENABLE_CODESNIPPET = True
    CODEMIRROR_LANGUAGES = ['python', "c", 'html']  # optional
    CODEMIRROR_THEME = 'colorforth'
    CODEMIRROR_ADDONS = (('display', 'placeholder'),)
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql://root:123@127.0.0.1:3306/school"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql://root:123@127.0.0.1:3306/web2"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql://root:123@127.0.0.1:3306/school"


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

=======
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'you will never know the key'
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = '18294090'
    MAIL_PASSWORD = 'zh64581948'
    FLASKY_MAIL_SUBJECT_PREFIX = '[FLASKY]'
    FLASKY_MAIL_SENDER = '*****'
    FLASKY_ADMIN = '*****'
    BOOTSTRAP_BOOTSWATCH_THEME = 'yeti'  # bootstrap主题设置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CKEDITOR_FILE_UPLOADER = 'main.upload'
    CKEDITOR_ENABLE_CODESNIPPET = True
    CODEMIRROR_LANGUAGES = ['python', "c", 'html']  # optional
    CODEMIRROR_THEME = 'colorforth'
    CODEMIRROR_ADDONS = (('display', 'placeholder'),)
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql://root:123@127.0.0.1:3306/school"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql://root:123@127.0.0.1:3306/web2"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "mysql://root:123@127.0.0.1:3306/school"


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
>>>>>>> d989a01c055dd7066c1fb6cabda1c43d81584f09
