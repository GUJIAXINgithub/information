from flask import render_template, current_app, session, jsonify

from info import constants
from info.modules.index import index_blue
from info.models import User, News
from info.utils.response_code import RET


@index_blue.route('/')
def index():
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

    data = {
        "user": user.to_dict() if user else None
    }

    # 获取点击排行
    news_li = list()
    news_dict_li = list()
    try:
        news_li = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    for news in news_li:
        news_dict_li.append(news.to_basic_dict())

    return render_template('news/index.html',
                           data=data,
                           news_dict_li=news_dict_li)


@index_blue.route('/favicon.ico')
def favicon():
    # send_static_file是flask中请求静态文件的方法
    return current_app.send_static_file('news/favicon.ico')
