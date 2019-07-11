from flask import Blueprint

center_blue = Blueprint('center', __name__, url_prefix='/user')

from .views import *
