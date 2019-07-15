from flask import render_template, current_app, jsonify, g, request
from info import db
from info.models import Comment, CommentLike, User
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
    # 默认没有关注作者
    is_followed = False
    # 根据新闻id查询新闻
    news = get_news(news_id)
    news.clicks += 1

    user = g.user

    if user:
        # 判断当前用户是否收藏
        if news in user.collection_news:
            is_collect = True
        # 判断当前用户是关注作者
        if news.user in user.followed:
            is_followed = True

    news = news.to_dict()

    # 获取当前新闻的所有评论信息
    comments = list()

    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_dict_li = list()

    for comment in comments:
        comment_dict = comment.to_dict()
        # 默认没有点攒
        comment_dict['is_like'] = False
        if user:
            # 查询当前用户是否点攒了当前评论
            comment_like = None
            try:
                comment_like = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                        CommentLike.comment_id == comment.id).first()
            except Exception as e:
                current_app.logger.error(e)

            if comment_like:
                comment_dict['is_like'] = True

        comment_dict_li.append(comment_dict)

    data = {
        "user": user.to_dict() if user else None,
        'news': news,
        'is_collect': is_collect,
        'is_followed': is_followed,
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
    else:
        return jsonify(errno=RET.DATAEXIST, errmsg='错误的操作')

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
    comment_info = resp.get('comment')
    parent_id = resp.get('parent_id')

    # 校验参数
    if not all([news_id, comment_info]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据新闻id查询新闻，校验是否存在
    get_news(news_id)

    # 初始化评论模型
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_info
    if parent_id:
        try:
            parent_id = int(parent_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        comment.parent_id = parent_id

    # 将数据添加到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    data = comment.to_dict()

    return jsonify(errno=RET.OK, errmsg='评论成功', data=data)


@news_blue.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    """
    点赞和取消点赞功能
    :return: json
    """
    # 校验用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 获取参数
    resp = request.json
    comment_id = resp.get('comment_id')
    action = resp.get('action')

    # 校验参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    if action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据comment_id查询评论，校验是否存在
    comment = None

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg='评论不存在')

    # 代码执行到此说明用户登录，且评论存在
    # 查询当前评论是否被当前用户点攒
    try:
        comment_like = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                CommentLike.comment_id == comment_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询错误')

    if action == 'add' and not comment_like:
        # 生成点攒
        new_comment_like = CommentLike()
        new_comment_like.user_id = user.id
        new_comment_like.comment_id = comment_id
        db.session.add(new_comment_like)
        # 点赞数+1
        comment.like_count += 1

    elif action == 'remove' and comment_like:
        # 删除点攒
        db.session.delete(comment_like)
        # 点赞数-1
        comment.like_count -= 1

    else:
        return jsonify(errno=RET.DATAEXIST, errmsg='错误的操作')

    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blue.route('/followed_user', methods=['POST'])
@user_login_data
def followed_user():
    """
    关注与取消关注
    :return:
    """
    # 判断登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="未登录")

    # 获取参数
    author_id = request.json.get("user_id")
    action = request.json.get("action")

    # 校验参数
    if not all([author_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询作者
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    if not author:
        return jsonify(errno=RET.NODATA, errmsg="数据错误")

    if action == "follow" and author not in user.followed:
        user.followed.append(author)
    elif action == "unfollow" and author in user.followed:
        user.followed.remove(author)
    else:
        return jsonify(errno=RET.DATAEXIST, errmsg='错误的操作')

    # 保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据错误")

    return jsonify(errno=RET.OK, errmsg="操作成功")
