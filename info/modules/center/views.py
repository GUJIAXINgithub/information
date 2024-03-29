from flask import render_template, g, redirect, request, jsonify, current_app, session, abort
from info import db, constants
from info.models import Category, News, User
from info.modules.center import center_blue
from info.utils.common import user_login_data, db_commit
from info.utils.image_storage import storage
from info.utils.response_code import RET


@center_blue.route('/info')
@user_login_data
def user_center():
    """
    用户中心页
    :return:
    """
    # 判断用户是否登录
    user = g.user
    if not user:
        return redirect('/')

    data = {
        'user': user.to_dict()
    }

    return render_template('news/user.html', data=data)


@center_blue.route('/base_info', methods=["get", "post"])
@user_login_data
def base_info():
    """
    修改个人信息页面
    :return: 'POST'=json
    """
    user = g.user
    if not user:
        return redirect('/')

    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('news/user_base_info.html', data=data)

    elif request.method == 'POST':
        # 获取参数
        resp = request.json
        nick_name = resp.get('nick_name')
        signature = resp.get('signature')
        gender = resp.get('gender')

        # 校验参数
        if not all([nick_name, signature, gender]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

        if len(nick_name) > 32 or len(signature) > 128 or gender not in ['MAN', 'WOMAN']:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        user.nick_name = nick_name
        user.signature = signature
        user.gender = gender

        db_commit(db)

        return jsonify(errno=RET.OK, errmsg='更新成功')


@center_blue.route('/pic_info', methods=["get", "post"])
@user_login_data
def pic_info():
    """
    修改头像页面
    :return: 'POST'=json
    """
    user = g.user
    if not user:
        return redirect('/')

    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('news/user_pic_info.html', data=data)

    elif request.method == 'POST':
        # 获取参数
        try:
            avatar = request.files.get('avatar').read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg='数据错误')

        # 上传图片
        try:
            url = storage(avatar)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg='上传失败')

        # 将url保存到数据库
        user.avatar_url = url
        db_commit(db)

        data = {
            'avatar_url': constants.QINIU_DOMIN_PREFIX + url
        }

        return jsonify(errno=RET.OK, errmsg='上传成功', data=data)


@center_blue.route('/pass_info', methods=["get", "post"])
@user_login_data
def pass_info():
    """
    修改密码页面
    :return: 'POST'=json
    """
    user = g.user
    if not user:
        return redirect('/')

    if request.method == 'GET':
        return render_template('news/user_pass_info.html')

    elif request.method == 'POST':
        # 获取参数
        resp = request.json
        old_password = resp.get('old_password')
        new_password = resp.get('new_password')

        # 校验参数
        if not all(['old_password', 'new_password']):
            return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

        # 校验密码
        if user.check_password(old_password):
            user.password = new_password
        else:
            return jsonify(errno=RET.PWDERR, errmsg='密码错误')

        db_commit(db)

        # 密码修改成功后，修改session中的信息
        session['id'] = user.id
        session['password'] = user.password_hash

        return jsonify(errno=RET.OK, errmsg='密码修改成功')


@center_blue.route('/collection')
@user_login_data
def user_collection():
    """
    用户中心关注页面
    :return: json
    """
    user = g.user
    if not user:
        return redirect('/')

    # 获取参数
    page = request.args.get('p', 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 设置默认值
    total_page = 1
    current_page = 1
    item_list = list()

    try:
        paginates = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        # 总页数
        total_page = paginates.pages
        # 当前页
        current_page = paginates.page
        # 当前页内容
        item_list = paginates.items

    except Exception as e:
        current_app.logger.error(e)

    collection_dict_li = list()

    for item in item_list:
        collection_dict_li.append(item.to_basic_dict())

    data = {
        'current_page': current_page,
        'total_page': total_page,
        'collections': collection_dict_li
    }

    return render_template('news/user_collection.html', data=data)


@center_blue.route('/news_release', methods=["get", "post"])
@user_login_data
def news_release():
    """
    用户中心发布新闻页
    :return: 'POST'=json
    """
    if request.method == 'GET':
        # 查询新闻种类
        categories = list()
        try:
            categories = Category.query.filter(Category.id != 1).all()
        except Exception as e:
            current_app.logger.error(e)

        category_dict_li = list()
        for item in categories:
            category_dict_li.append(item.to_dict())

        data = {
            'categories': category_dict_li
        }

        return render_template('news/user_news_release.html', data=data)

    elif request.method == 'POST':
        # 校验登录
        user = g.user
        if not user:
            return redirect('/')

        # 获取参数
        resp = request.form
        title = resp.get('title')
        category_id = resp.get('category_id')
        digest = resp.get('digest')
        index_image = request.files.get('index_image')
        content = resp.get('content')

        # 校验参数
        if not all([title, category_id, digest, index_image, content]):
            return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

        try:
            category_id = int(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        if len(title) > 256 or len(digest) > 512:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        # 读取图片, 存入七牛
        try:
            index_image = index_image.read()
            index_image_url = constants.QINIU_DOMIN_PREFIX + storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg='上传图片错误')

        # 初始化新闻对象
        news = News()
        news.title = title
        news.category_id = category_id
        news.digest = digest
        news.index_image_url = index_image_url
        news.content = content
        news.source = '个人发布'
        news.user_id = user.id
        news.status = 1

        # 将对象保存到数据库
        db.session.add(news)
        db_commit(db)

        return jsonify(errno=RET.OK, errmsg='新闻发布成功等待审核')


@center_blue.route('/news_list')
@user_login_data
def news_list():
    """
    个人中心用户新闻列表
    :return:
    """
    # 校验登录
    user = g.user
    if not user:
        return redirect('/')

    # 获取参数
    page = request.args.get('p', 1)

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据参数查询数据库
    # 设置默认值
    total_page = 1
    current_page = 1
    item_list = list()

    try:
        paginates = user.news_list.paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # paginate = News.query.filter(News.user_id == user.id).paginate(page,
        #                                                                constants.OTHER_NEWS_PAGE_MAX_COUNT,
        #                                                                False)
        # 总页数
        total_page = paginates.pages
        # 当前页
        current_page = paginates.page
        # 当前页内容
        item_list = paginates.items
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = list()
    for item in item_list:
        news_dict_list.append(item.to_review_dict())

    data = {
        'current_page': current_page,
        'total_page': total_page,
        'news_list': news_dict_list  # FIXME: item_list
    }

    return render_template('news/user_news_list.html', data=data)


@center_blue.route('/user_follow')
@user_login_data
def user_follow():
    """
    个人中心我的关注
    :return:
    """
    # 校验登录
    user = g.user
    if not user:
        return redirect('/')

    # 获取参数
    page = request.args.get("p", 1)

    # 校验参数
    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据参数查询数据库
    # 设置默认值
    current_page = 1
    total_page = 1
    follows = list()

    try:
        paginates = user.followed.paginate(page, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 当前页数据
        follows = paginates.items
        # 当前页
        current_page = paginates.page
        # 总页数
        total_page = paginates.pages
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = list()
    for user_ in follows:
        user_dict_li.append(user_.to_dict())

    data = {
        "users": user_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return render_template('news/user_follow.html', data=data)


@center_blue.route('/other_info')
@user_login_data
def other_info():
    """
    其他用户信息页
    :return:
    """
    # 获取其他用户id
    other_id = request.args.get("id")
    if not other_id:
        abort(404)

    # 查询用户模型
    other = None

    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)

    if not other:
        abort(404)

    # 判断当前登录用户是否关注过other
    is_followed = False
    user = g.user

    if user and other in user.followed:
        is_followed = True

    data = {
        "user": user.to_dict(),
        "other_info": other.to_dict(),
        "is_followed": is_followed
    }
    return render_template('news/other.html', data=data)


@center_blue.route('/other_news_list')
def other_news_list():
    """
    其他用户界面新闻列表
    :return:
    """
    # 获取参数
    page = request.args.get("p", 1)
    user_id = request.args.get("user_id")

    # 校验参数
    if not all([page, user_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询用户
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询错误")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    # 根据参数查询数据库
    # 设置默认值
    current_page = 1
    total_page = 1
    news_li = list()

    try:
        paginate = News.query.filter(News.user_id == user.id)\
            .paginate(page, constants.OTHER_NEWS_PAGE_MAX_COUNT, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = list()
    for news_ in news_li:
        news_dict_li.append(news_.to_review_dict())

    data = {
        "news_list": news_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return jsonify(errno=RET.OK, errmsg="OK", data=data)
