# File: library_api/v2/__init__.py

from flask import Blueprint

bp = Blueprint('v2', __name__)

from . import routes_demo