from info import redis_store
from info.modules.index import index_blue


@index_blue.route('/')
def index():
    redis_store.set('name', 'TOM')
    return 'index'
