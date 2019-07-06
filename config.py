import logging

from redis import StrictRedis


class Config(object):
    """项目配置"""
    # 设置secret_key  # base64.b64encode(os.urandom(48)
    SECRET_KEY = 'KfgaH5AEwtOCqYTczLGyItJvISts5svLlfFgK+jar0wsg3R820Whyuh9yTSnxQAZ'

    # 配置mysql
    SQLALCHEMY_DATABASE_URI = 'mysql://root:429005@localhost:3306/information'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置Redis
    REDIS_HOST = '127.0.0.1'
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

    # 配置默认log等级
    LOG_LEVEL = logging.DEBUG


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 设置log等级
    LOG_LEVEL = logging.ERROR


class TestingConfig(Config):
    """单元测试环境配置"""
    DEBUG = True
    # 设置log等级
    LOG_LEVEL = logging.WARNING


# 设置一个字典存放不同的配置类型
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
