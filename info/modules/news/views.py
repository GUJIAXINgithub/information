from flask import render_template, current_app, jsonify, g, request
from info import db
from info.models import Comment
from info.modules.news import news_blue
from info.utils.common import user_login_data, click_list_info, get_news
from info.utils.response_code import RET


@news_blue.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    """
    新闻详情页面
    :param news_id:
    :return:
    """
    # 默认没有收藏新闻
    is_collect = False
    # 根据新闻id查询新闻
    news = get_news(news_id)
    news.clicks += 1

    # 判断当前用户是否收藏
    user = g.user

    if user:
        if news in user.collection_news:
            is_collect = True

    news = news.to_dict()

    # 获取当前新闻的评论信息
    comments = list()

    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_dict_li = list()

    for comment in comments:
        comment_dict_li.append(comment.to_dict())

    data = {
        "user": user.to_dict() if user else None,
        'news': news,
        'is_collect': is_collect,
        'news_dict_li': click_list_info(),
        'comments': comment_dict_li
    }

    return render_template('news/detail.html', data=data)


@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    """
    收藏和取消收藏
    :return: json
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

    # 根据新闻id查询新闻
    news = get_news(news_id)

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


@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    """
    评论新闻
    :return: json
    """
    # 判断是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 获取参数
    resp = request.json
    news_id = resp.get('news_id')
    comment = resp.get('comment')
    parent_id = resp.get('parent_id')

    # 校验参数
    if not all([news_id, comment]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据新闻id查询新闻
    news = get_news(news_id)

    # 初始化评论模型，保存数据
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = comment
    if parent_id:
        comment.parent_id = parent_id

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    return jsonify(errno=RET.OK, errmsg='评论成功', data=comment.to_dict())
