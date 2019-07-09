import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from redis import StrictRedis
from config import config

# 创建mysql数据库对象

db = SQLAlchemy()

# 创建Redis对象全局变量
redis_store = None  # type:StrictRedis


# 使用工厂方法创建app实例
def create_app(config_name):
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化mysql数据库对象
    db.init_app(app)
    # 初始化Redis数据库对象
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST,
                              port=config[config_name].REDIS_PORT,
                              db=0,
                              decode_responses=True)
    # 开启CSRF保护
    CSRFProtect(app)

    @app.after_request
    def after_request(response):
        """
        CSRFProtect只验证request中的csrf_token和cookie中的csrf_token是否一致，
        cookie中的csrf_token和表单/request中的csrf_token需要我们自己实现
        """
        # 生成一个csrf_token
        csrf_token = generate_csrf()
        # 将csrf_token存入cookie
        response.set_cookie('csrf_token', csrf_token)
        return response

    # 设置session保存指定的位置
    Session(app)

    # 配置项目日志
    setup_log(config_name)

    # 将蓝图注册到app中
    from info.modules.index import index_blue
    app.register_blueprint(index_blue)

    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    from info.modules.news import news_blue
    app.register_blueprint(news_blue)

    # 注册自定义过滤器
    from info.utils.common import index_to_class
    app.add_template_filter(index_to_class, 'index_to_class')

    return app


# 配置日志
def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
