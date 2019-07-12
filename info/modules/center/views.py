from flask import render_template, g, redirect, request, jsonify, current_app
from info import db, constants
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
    :return:
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
