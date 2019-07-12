import logging
from qiniu import Auth, put_data

access_key = '9AmGlC30LcN7D1zWVK-lvuqS3e8CfSMUd5gH1EMX'
secret_key = 'Dq_Sxis_jIwmYdKh9NLJhvRpnkZG5Ox8t1nnnDVm'

# 要上传的空间
bucket_name = 'testroom'


def storage(data):
    """
    七牛云上传图片
    :param data: 图片的二进制数据
    :return: 七牛中保存的图片名/路径
    """
    try:
        # 构建鉴权对象
        id = Auth(access_key, secret_key)
        # 生成上传 Token，可以指定过期时间等
        token = id.upload_token(bucket_name)
        # 上传文件
        ret, info = put_data(token, None, data)

    except Exception as e:
        logging.error(e)
        raise e

    if info and info.status_code != 200:
        raise Exception("上传失败")

    # 返回七牛中保存的图片名，这个图片名也是访问七牛获取图片的路径
    return ret["key"]


if __name__ == '__main__':
    path = r'C:\Users\se7en\Downloads\18149663983_652f9c8b92_o.jpg'
    with open(path, "rb") as f:
        key = storage(f.read())

    print(key)