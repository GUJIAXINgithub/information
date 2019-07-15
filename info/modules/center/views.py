from flask import render_template, g, redirect, request, jsonify, current_app, session
from info import db, constants
from info.models import Category, News
from info.modules.center import center_blue
from info.utils.common import user_login_data
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
        try:
            user.avatar_url = url
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')

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
        try:
            db.session.add(news)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg='数据库错误')

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
