import re
from datetime import datetime
from random import randint
from flask import request, make_response, current_app, jsonify, abort, session
from info import redis_store, constants, db
from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.modules.passport import passport_blue
from info.utils.captcha.captcha import captcha
from info.utils.common import db_commit
from info.utils.response_code import RET


@passport_blue.route('/image_code')
def get_image_code():
    """
    注册页面请求图片验证码
    :return:
    """

    # 获取到当前的图片编号id
    code_id = request.args.get('imageCodeId', None)
    # 判断code_id是否有值
    if code_id is None:
        return abort(403)
    # 使用captcha生成图片验证码
    name, text, image = captcha.generate_captcha()

    # 将图片验证码的内容保存的Redis中
    try:
        redis_store.setex('ImageCode_' + code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 使用log记录
        current_app.logger.error(e)
        response = make_response(jsonify(errno=RET.DATAERR, errmsg='保存验证码失败'))
        return response

    # 将图片验证码加入响应报文
    response = make_response(image)
    # 设置响应报文类型
    response.headers['Content-Type'] = 'image/jpg'

    return response


@passport_blue.route('/sms_code', methods=['POST'])
def send_sms():
    """
    注册页面请求短信验证码
    :return:
    """

    # 接收参数并判断是否有值
    resp = request.json
    mobile = resp.get('mobile')
    image_code = resp.get('image_code')
    image_code_id = resp.get('image_code_id')

    if not all([mobile, image_code, image_code_id]):
        # 参数不全
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    # 校验手机号是否正确
    if not re.match(r'^1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号不正确')

    # 验证该手机号是否已经注册
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询错误')

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg='该手机号已经注册')

    # 通过image_code_id去redis中查询真实的image_code
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询失败')

    # 判断验证码是否过期
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已失效')

    # 进行验证码内容的比对
    if image_code.upper() != real_image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 生成发送短信的内容并发送短信
    # sms_code = '%06d' % randint(0, 999999)
    sms_code = '000000'
    # TODO: 发短信
    print('sms_code:', sms_code)
    # result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR, errmsg='短信发送失败')

    # redis中保存短信验证码内容
    try:
        redis_store.setex('SMSCode_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)  # 使用log记录
        return jsonify(errno=RET.DATAERR, errmsg='保存验证码失败')

    # 返回发送成功的响应
    return jsonify(errno=RET.OK, errmsg='短信验证码发送成功')


@passport_blue.route('/register', methods=['POST'])
def register():
    """
    点击注册实现验证并注册
    :return:
    """
    # 获取参数和判断是否有值
    resp = request.json
    mobile = resp.get('mobile')
    sms_code = resp.get('sms_code')
    password = resp.get('password')

    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    # 从Redis中获取指定手机号对应的短信验证码的
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询失败')

    # 判断验证码是否过期
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已失效')

    # 校验验证码
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 初始化user模型，并设置数据并添加到数据库
    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.create_time = datetime.now()
    user.last_login = datetime.now()
    # 设置password属性会自动设置password_hash
    user.password = password

    # 保存当前用户的状态
    db.session.add(user)
    db_commit(db)

    # 保存用户登录状态
    session['id'] = user.id
    session['password'] = user.password_hash
    session['is_admin'] = user.is_admin

    # 返回注册的结果
    return jsonify(errno=RET.OK, errmsg='注册成功')


@passport_blue.route('/login', methods=['POST'])
def login():
    """
    登录功能逻辑
    :return:
    """
    # 获取参数和判断是否有值
    resp = request.json
    mobile = resp.get('mobile')
    password = resp.get('password')

    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    # 判断手机号是否合法
    if not re.match(r'^1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='用户不存在')

    # 从数据库查询出指定的用户
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询失败')

    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='用户不存在')

    # 校验密码
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg='用户名或密码错误')

    # 保存用户登录状态
    session['id'] = user.id
    session['password'] = user.password_hash
    session['is_admin'] = user.is_admin

    # 记录用户最后一次登录时间  # FIXME: 逻辑需要修正
    user.last_login = datetime.now()
    db_commit(db)

    return jsonify(errno=RET.OK, errmsg='登陆成功')


@passport_blue.route('/logout')
def logout():
    """
    登出功能，清除session中的kv
    :return:
    """
    session['id'] = None
    session['password'] = None
    session['is_admin'] = False
    return jsonify(errno=RET.OK, errmsg='登出成功')
