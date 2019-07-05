from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_session import Session  # 用来指定session保存的位置
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from redis import StrictRedis
from flask_script import Manager


class Config(object):
    """项目配置"""
    DEBUG = True
    # 设置secret_key  # base64.b64encode(os.urandom(48)
    SECRET_KEY = 'KfgaH5AEwtOCqYTczLGyItJvISts5svLlfFgK+jar0wsg3R820Whyuh9yTSnxQAZ'

    # 配置mysql
    SQLALCHEMY_DATABASE_URI = 'mysql://root:429005@localhost:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置Redis
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379

    # 设置session保存位置
    SESSION_TYPE = 'redis'

    # 指定session保存的Redis
    # SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

    # 设置开启session签名
    SESSION_SIGNER = True

    # 设置session需要过期
    SESSION_PERMANENT = False

    # 设置session过期时间(参数在Flask中)
    PERMANENT_SESSION_LIFETIME = 86400 * 2


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
# 创建中断命令对象
manager = Manager(app)
# 将使用迁移类将应用对象app和数据库对象保存起来
Migrate(app, db)
# 将数据库迁移的命令添加到manager中
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    return 'index'


if __name__ == '__main__':
    manager.run()
