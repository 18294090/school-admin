from flask import Blueprint
job_manage = Blueprint("job", __name__)
from . import views