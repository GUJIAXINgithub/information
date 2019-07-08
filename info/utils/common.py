def index_to_class(index):
    """
    自定义过滤器
    :return:
    """
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ''