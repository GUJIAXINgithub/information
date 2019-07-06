import re
from random import randint
from flask import request, make_response, current_app, jsonify
from info import redis_store, constants
from info.lib.yuntongxun.sms import CCP
from info.modules.passport import passport_blue
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET


@passport_blue.route('/image_code')
def get_image_code():
    """
    注册页面请求图片验证码
    :return:
    """

    # 获取到当前的图片编号id
    code_id = request.args.get('code_id')
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


@passport_blue.route('/sms_code')
def send_sms():
    """
    1. 接收参数并判断是否有值
    2. 校验手机号是正确
    3. 通过传入的图片编码去redis中查询真实的图片验证码内容
    4. 进行验证码内容的比对
    5. 生成发送短信的内容并发送短信
    6. redis中保存短信验证码内容
    7. 返回发送成功的响应
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
    if not re.match('^1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR, errmsg='手机号不正确')

    # 通过image_code_id去redis中查询真实的image_code
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)  # 使用log记录
        return jsonify(errno=RET.DATAERR, errmsg='查询失败')

    # 判断验证码是否过期
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已失效')

    # 进行验证码内容的比对
    if image_code.upper() != real_image_code.upper():
        return jsonify(errno=RET.DATAERR, errmsg='验证码错误')

    # 生成发送短信的内容并发送短信
    sms_code = '%06d' % randint(0, 999999)
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg='短信发送失败')

    # redis中保存短信验证码内容
    try:
        redis_store.setex('SMSCode_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)  # 使用log记录
        return jsonify(errno=RET.DATAERR, errmsg='保存验证码失败')

    # 返回发送成功的响应
    return jsonify(errno=RET.OK, errmsg='短信验证码发送成功')
