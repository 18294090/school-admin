from flask import Blueprint
examination = Blueprint("examination", __name__)
from . import views