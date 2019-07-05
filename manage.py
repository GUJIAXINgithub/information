from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from info import create_app, db

# 通过指定配置的名字，创建对应配置的app
app = create_app('development')

# 创建终端命令对象
manager = Manager(app)
# 将使用迁移类将应用对象app和数据库对象保存起来
Migrate(app, db)
# 将数据库迁移的命令添加到manager中
manager.add_command('db', MigrateCommand)


@app.route('/')
def index():
    return 'index'


if __name__ == '__main__':
    manager.run()
