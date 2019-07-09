from flask import render_template

from info.modules.news import news_blue


@news_blue.route('/<int:news_id>')
def news_detail(news_id):
    """
    新闻详情页面
    :param news_id:
    :return:
    """
    return render_template('news/detail.html')
