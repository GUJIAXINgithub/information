from flask import request, make_response, current_app, jsonify

from info import redis_store, constants
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
