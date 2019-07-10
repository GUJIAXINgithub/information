from flask import render_template, current_app, session, jsonify, request, g
from info import constants
from info.modules.index import index_blue
from info.models import User, News, Category
from info.utils.common import user_login_data
from info.utils.response_code import RET


@index_blue.route('/favicon.ico')
def favicon():
    # send_static_file是flask中请求静态文件的方法
    return current_app.send_static_file('news/favicon.ico')


@index_blue.route('/')
@user_login_data
def index():
    """
    从session中获取用户id，如果有，查询用户信息
    查询点击排行，获取新闻信息
    查询新闻分类信息
    :return: data:字典 存储了以上信息
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

    # 获取新闻分类
    category_li = list()
    try:
        category_li = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    category_dict_li = list()
    for category in category_li:
        category_dict_li.append(category.to_dict())

    data = {
        "user": user.to_dict() if user else None,
        'news_dict_li': news_dict_li,
        'category_dict_li': category_dict_li
    }

    return render_template('news/index.html', data=data)


@index_blue.route('/news_list')
def news_list():
    """
    查询新闻列表返回给前端
    :return: json
    """
    # 获取参数
    resp = request.args

    cid = resp.get('cid', 1)  # 分类id，默认为1
    page = resp.get('page', 1)  # 页数，不传即获取第1页
    per_page = resp.get('per_page', "10")  # 每页多少条数据，默认10条

    # 校验获取的参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据参数查询数据库
    filters = list()
    if cid != 1:
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询错误')

    news_row_list = paginate.items  # 当前页模型对象列表
    total_pages = paginate.pages  # 总页数
    current_page = paginate.page  # 当前页

    news_dict_li = list()
    for news_row in news_row_list:
        news_dict_li.append(news_row.to_basic_dict())

    data = {
        "current_page": current_page,
        "total_pages": total_pages,
        "news_dict_li": news_dict_li
    }

    return jsonify(errno=RET.OK, errmsg='OK', data=data)
