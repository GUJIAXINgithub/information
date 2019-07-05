import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_session import Session  # 用来指定session保存的位置
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import config

# 创建mysql数据库对象
db = SQLAlchemy()


# 使用工厂方法创建app实例
def create_app(config_name):
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化mysql数据库对象
    db.init_app(app)
    # 初始化Redis数据库对象
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)
    # 开启CSRF保护
    CSRFProtect(app)
    """
    CSRFProtect只做验证工作，
    cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
    """
    # 设置session保存指定的位置
    Session(app)

    # 配置项目日志
    setup_log(config_name)

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