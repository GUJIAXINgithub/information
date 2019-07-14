from flask import render_template, request, jsonify, current_app, session, redirect, g, url_for

from info.models import User
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
            return render_template('admin/index.html')

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
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

        try:
            user = User.query.filter(User.mobile == username).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询错误')

        if not user:
            return jsonify(errno=RET.NODATA, errmsg='用户名或密码错误')

        if not user.check_password(password):
            return jsonify(errno=RET.PWDERR, errmsg='用户名或密码错误')

        if not user.is_admin:
            return jsonify(errno=RET.ROLEERR, errmsg='禁止非管理员登录')

        session['id'] = user.id
        session['is_admin'] = user.is_admin
        session['password'] = user.password_hash

        return redirect(url_for('admin.index'))


@admin_blue.route('/logout', methods=["GET", "POST"])
def admin_logout():
    """
    管理员登出
    :return:
    """
    session.pop('id')
    session.pop('password')
    session.pop('is_admin')
    return redirect(url_for('admin.admin_login'))
