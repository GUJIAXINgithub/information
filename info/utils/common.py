import functools

from flask import session, current_app, jsonify, g

from info.models import User
from info.utils.response_code import RET


def index_to_class(index):
    """
    自定义过滤器
    :return:
    """
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ''


def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # 从session中获取用户的id
        user = None
        user_id = session.get('id', None)

        # 通过id获取用户信息，传给后台
        if user_id:
            try:
                user = User.query.filter(User.id == user_id).first()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg='查询失败')

        g.user = user

        return f(*args, **kwargs)

    return wrapper
