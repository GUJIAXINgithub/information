import functools
from flask import session, current_app, jsonify, g, abort, redirect, url_for
from info import constants
from info.models import User, News
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

        # 通过id获取用户信息
        if user_id:
            try:
                user = User.query.filter(User.id == user_id).first()
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg='查询失败')

        g.user = user

        return f(*args, **kwargs)

    return wrapper


def click_list_info():
    """
    获取点击排行
    :return: news_dict_li
    """
    news_li = list()
    try:
        news_li = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = list()
    for item in news_li:
        news_dict_li.append(item.to_basic_dict())

    return news_dict_li


def get_news(news_id):
    """
    根据新闻id查询新闻
    :param news_id:
    :return: news
    """
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    news = None

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        abort(404)

    return news


def check_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get('id', None)

        if user_id:
            user = None
            try:
                user = User.query.filter(User.id == user_id).first()
            except Exception as e:
                current_app.logger.error(e)

            if not user:
                return redirect(url_for('index.index'))
            elif not user.is_admin:
                return redirect(url_for('index.index'))
            else:
                # 该用户在数据库中存在，且是管理员
                g.user = user
        else:
            g.user = None

        return f(*args, **kwargs)

    return wrapper
