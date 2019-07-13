from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from info import create_app, db
from info.models import User

# 通过指定配置的名字，创建对应配置的app

app = create_app('development')

# 创建终端命令对象
manager = Manager(app)
# 将使用迁移类将应用对象app和数据库对象保存起来
Migrate(app, db)
# 将数据库迁移的命令添加到manager中
manager.add_command('db', MigrateCommand)


@manager.option('-n', '-name', dest='user_name')
@manager.option('-p', '-password', dest='password')
def createsuperuser(user_name, password):
    """
    创建管理员账户
    :param user_name: 用户名
    :param password: 密码
    :return:
    """
    if not all([user_name, password]):
        print('缺少参数：-n "用户名" -p "密码"')

    # 初始化用户对象
    user = User()
    user.mobile = user_name
    user.nick_name = user_name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print('创建管理员成功')
    except Exception as e:
        db.session.rollback()
        raise e


if __name__ == '__main__':
    manager.run()
    # app.run()
