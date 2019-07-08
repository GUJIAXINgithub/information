from flask import render_template, current_app, session, jsonify
from info.modules.index import index_blue
from info.models import User
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

    return render_template('news/index.html',
                           data=data)


@index_blue.route('/favicon.ico')
def favicon():
    # send_static_file是flask中请求静态文件的方法
    return current_app.send_static_file('news/favicon.ico')
