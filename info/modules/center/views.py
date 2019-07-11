from flask import render_template

from info.modules.center import center_blue
from info.utils.common import user_login_data


@center_blue.route('/info')
@user_login_data
def user_info():
    data = {

    }
    return render_template('news/user.html', data=data)