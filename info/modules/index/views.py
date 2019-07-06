from flask import render_template

from info import redis_store
from info.modules.index import index_blue


@index_blue.route('/')
def index():
    return render_template('news/index.html')
