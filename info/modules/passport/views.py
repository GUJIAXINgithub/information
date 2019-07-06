from info.modules.passport import passport_blue


@passport_blue.route('/')
def passport():
    return