from flask import Blueprint
pedagogical_analysis = Blueprint("pedagogical_analysis", __name__)
from . import views