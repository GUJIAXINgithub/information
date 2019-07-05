from flask import Flask
from flask_session import Session  # 用来指定session保存的位置
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from config import Config

app = Flask(__name__)
# 加载配置
app.config.from_object(Config)
# 初始化mysql数据库对象
db = SQLAlchemy(app)
# 初始化Redis数据库对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
# 开启CSRF保护
CSRFProtect(app)
"""
CSRFProtect只做验证工作，
cookie中的 csrf_token 和表单中的 csrf_token 需要我们自己实现
"""
# 设置session保存指定的位置
Session(app)
