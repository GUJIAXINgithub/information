from flask import render_template, session, current_app, jsonify, g, abort, request

from info import constants, db
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
    # 获取新闻详情
    news = None
    # 默认没有收藏新闻
    is_collect = False

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if news:
        news.clicks += 1
    else:
        abort(404)

    # 判断当前用户是否收藏
    user = g.user

    if user:
        if news in user.collection_news:
            is_collect = True

    news = news.to_dict()

    # 获取点击排行
    news_li = list()
    try:
        news_li = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = list()
    for item in news_li:
        news_dict_li.append(item.to_basic_dict())

    data = {
        "user": user.to_dict() if user else None,
        'news': news,
        'news_dict_li': news_dict_li,
        'is_collect': is_collect
    }

    return render_template('news/detail.html', data=data)


@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    """
    收藏和取消收藏
    :return:
    """
    # 判断是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 获取参数
    resp = request.json
    news_id = resp.get('news_id')
    action = resp.get('action')

    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据新闻id查询新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        abort(404)

    # 代码执行到此说明用户已经登录，且新闻存在
    if action == 'cancel_collect' and news in user.collection_news:
        user.collection_news.remove(news)
    elif action == 'collect' and news not in user.collection_news:
        user.collection_news.append(news)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    return jsonify(errno=RET.OK, errmsg='收藏成功')
