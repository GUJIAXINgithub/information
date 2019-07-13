from flask import render_template

from info.modules.admin import admin_blue


@admin_blue.route('/login')
def admin_login():
    return render_template('admin/login.html')
