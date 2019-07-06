from flask import render_template, current_app

from info import redis_store
from info.modules.index import index_blue


@index_blue.route('/')
def index():
    return render_template('news/index.html')


@index_blue.route('/favicon.ico')
def favicon():
    # send_static_file是flask中请求静态文件的方法
    return current_app.send_static_file('news/favicon.ico')
