import datetime
import time

from flask import render_template, request, current_app, session, redirect, g, url_for, jsonify
from sqlalchemy import and_

from info import constants, db
from info.models import User, News
from info.modules.admin import admin_blue
from info.utils.common import check_admin
from info.utils.response_code import RET


@admin_blue.route('/')
@check_admin
def index():
    # 校验是否登录
    password = session.get('password', None)
    user = g.user

    if user:
        if user.password_hash == password:
            data = {
                'user': user.to_dict()
            }
            return render_template('admin/index.html', data=data)

    return redirect(url_for('admin.admin_login'))


@admin_blue.route('/login', methods=["GET", "POST"])
@check_admin
def admin_login():
    """
    管理员登录页面
    :return:
    """
    if request.method == 'GET':
        # 校验是否登录
        password = session.get('password', None)
        user = g.user

        if user:
            if user.password_hash == password:
                return redirect(url_for('admin.index'))

        return render_template('admin/login.html')

    elif request.method == 'POST':
        # 获取参数
        resp = request.form
        username = resp.get('username')
        password = resp.get('password')

        if not all([username, password]):
            return render_template('admin/login.html', errno=RET.PARAMERR, errmsg='参数错误')

        try:
            user = User.query.filter(User.mobile == username).first()
        except Exception as e:
            current_app.logger.error(e)
            return render_template('admin/login.html', errno=RET.DBERR, errmsg='查询错误')

        if not user:
            return render_template('admin/login.html', errno=RET.NODATA, errmsg='用户名或密码错误')

        if not user.check_password(password):
            return render_template('admin/login.html', errno=RET.PWDERR, errmsg='用户名或密码错误')

        if not user.is_admin:
            return render_template('admin/login.html', errno=RET.ROLEERR, errmsg='禁止非管理员登录')

        session['id'] = user.id
        session['is_admin'] = user.is_admin
        session['password'] = user.password_hash

        data = {
            'user': user.to_dict()
        }

        return render_template('admin/index.html', data=data)


@admin_blue.route('/logout', methods=["GET", "POST"])
def admin_logout():
    """
    管理员登出
    :return:
    """
    session['id'] = None
    session['password'] = None
    session['is_admin'] = False
    return redirect(url_for('admin.admin_login'))


@admin_blue.route('/user_count')
@check_admin
def user_count():
    """
    用户统计页面数据展示
    :return:
    """
    # 获取总用户数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    now = time.localtime()
    # 获取月增用户数
    mon_count = 0
    try:
        mon_begin_str = "%d-%02d-01" % (now.tm_year, now.tm_mon)
        mon_begin_date = datetime.datetime.strptime(mon_begin_str, '%Y-%m-%d')
        mon_count = User.query.filter(User.is_admin == False,
                                      User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 获取日增用户数
    day_count = 0
    try:
        day_begin_str = "%d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday)
        day_begin_date = datetime.datetime.strptime(day_begin_str, '%Y-%m-%d')
        day_count = User.query.filter(User.is_admin == False,
                                      User.create_time >= day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 获取图标中需要的数据
    daily_date = []
    daily_count = []

    now_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    now_date = datetime.datetime.strptime(now_date_str, '%Y-%m-%d')

    for num in range(0, 31):
        date_begin = now_date - datetime.timedelta(days=num)
        date_end = now_date - datetime.timedelta(days=num - 1)

        count = 0
        try:
            count = User.query.filter(User.is_admin == False,
                                      and_(User.last_login >= date_begin, User.last_login < date_end)).count()
        except Exception as e:
            current_app.logger.error(e)

        daily_date.append(date_begin.strftime('%Y-%m-%d'))
        daily_count.append(count)

    daily_date.reverse()
    daily_count.reverse()

    data = {
        'total_count': total_count,
        'mon_count': mon_count,
        'day_count': day_count,
        'active_date': daily_date,
        'active_count': daily_count
    }

    return render_template('admin/user_count.html', data=data)


@admin_blue.route('/user_list')
@check_admin
def user_list():
    """
    用户列表页面数据展示
    :return:
    """
    # 获取参数
    page = request.args.get('p', 1)

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    current_page = 1
    total_page = 1
    user_list = list()

    try:
        paginates = User.query.filter(User.is_admin == False) \
            .order_by(User.last_login.desc()) \
            .paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)

        user_list = paginates.items
        current_page = paginates.page
        total_page = paginates.pages

    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = list()
    for user_ in user_list:
        user_dict_li.append(user_.to_admin_dict())

    data = {
        'current_page': current_page,
        'total_page': total_page,
        'user_list': user_dict_li
    }

    return render_template('admin/user_list.html', data=data)


@admin_blue.route('/news_review')
@check_admin
def news_review():
    """
    新闻审核页面
    :return:
    """
    # 获取参数
    page = request.args.get('p', 1)
    keywords = request.args.get('keywords', None)

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询数据库
    total_page = 1
    current_page = 1
    news_list = list()

    # 构建查询条件
    filters = [News.status != 0]
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginates = News.query.filter(*filters) \
            .order_by(News.status.desc(), News.create_time.asc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        current_page = paginates.page
        total_page = paginates.pages
        news_list = paginates.items

    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = list()
    for news_ in news_list:
        news_dict_li.append(news_.to_review_dict())

    data = {
        'current_page': current_page,
        'total_page': total_page,
        'news_list': news_dict_li
    }

    return render_template('admin/news_review.html', data=data)


@admin_blue.route('/news_review_detail')
@check_admin
def news_review_detail():
    """
    新闻审核详情页
    :return:
    """
    # 获取新闻id
    news_id = request.args.get('news_id', None)

    # 校验参数
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return redirect(url_for('admin.news_review'))

    # 通过id查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return redirect(url_for('admin.news_review'))

    # 校验新闻是否存在
    if not news:
        return redirect(url_for('admin.news_review'))

    # 校验新闻状态
    if news.status == 0:
        return redirect(url_for('admin.news_review'))

    data = {
        'news': news.to_dict()
    }

    return render_template('admin/news_review_detail.html', data=data)


@admin_blue.route('/make_review', methods=['POST'])
@check_admin
def make_review():
    """
    确认审核：accept/reject
    :return: json
    """
    # 接收参数
    resp = request.json
    news_id = resp.get('news_id')
    action = resp.get('action')
    reason = resp.get('reason', None)

    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据news_id查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询错误')

    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')

    if news.status != 1:
        return redirect(url_for('admin.news_review'))

    if action == 'accept':
        news.status = 0
    elif action == 'reject':
        if not reason:
            jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        else:
            news.status = -1
            news.reason = reason

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库错误')

    return jsonify(errno=RET.OK, errmsg='操作成功')


@admin_blue.route('/news_edit')
@check_admin
def news_edit():
    """
    新闻版式编辑页面
    :return:
    """
    # 获取参数
    page = request.args.get('p', 1)
    keywords = request.args.get('keywords', None)

    # 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 查询数据库
    total_page = 1
    current_page = 1
    news_list = list()

    # 构建查询条件
    filters = [News.status == 0]
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginates = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        current_page = paginates.page
        total_page = paginates.pages
        news_list = paginates.items

    except Exception as e:
        current_app.logger.error(e)

    news_dict_li = list()
    for news_ in news_list:
        news_dict_li.append(news_.to_basic_dict())

    data = {
        'current_page': current_page,
        'total_page': total_page,
        'news_list': news_dict_li
    }

    return render_template('admin/news_edit.html', data=data)
