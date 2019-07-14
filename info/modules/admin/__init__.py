from flask import Blueprint, url_for, g

admin_blue = Blueprint("admin", __name__, url_prefix='/admin')

from .views import *


# @admin_blue.before_request
# def check_admin():
#     """
#     校验用户是否是管理员
#     :return:
#     """
#     user_id = session.get('id', None)
#
#     if user_id:
#         user = None
#         try:
#             user = User.query.filter(User.id == user_id).first()
#         except Exception as e:
#             current_app.logger.error(e)
#
#         if not user:
#             return redirect(url_for('index.index'))
#         elif user.is_admin == False:
#             return redirect(url_for('index.index'))
#         else:
#             # 该用户在数据库中存在，且是管理员
#             g.user = user
#
#     g.user = None
