"""定义蓝图，作控制器，分发url请求"""

from flask import Blueprint
main = Blueprint("main", __name__)
from . import views, erros
