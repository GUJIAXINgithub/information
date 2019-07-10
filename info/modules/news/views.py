from flask import render_template, session, current_app, jsonify, g

from info import constants
from info.models import User, News
from info.modules.news import news_blue
from info.utils.common import user_login_data
from info.utils.response_code import RET


@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    """
    新闻详情页面
    :param news_id:
    :return:
    """
    user = g.user

    # 获取点击排行
    news_li = list()
    try:
        news_li = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = list()
    for news in news_li:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "user": user.to_dict() if user else None,
        'news_dict_li': news_dict_li
    }

    return render_template('news/detail.html', data=data)
