from flask import render_template, g, redirect

from info.modules.center import center_blue
from info.utils.common import user_login_data


@center_blue.route('/info')
@user_login_data
def user_info():
    """
    用户中心
    :return:
    """
    user = g.user
    if not user:
        return redirect('/')

    data = {
        'user': user.to_dict()
    }
    return render_template('news/user.html', data=data)
