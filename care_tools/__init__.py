from flask import Blueprint
care_tools_bp = Blueprint('care_tools', __name__, template_folder='../templates/care_tools')
from care_tools import routes