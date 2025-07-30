from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import posts, categories, tags, comments, errors