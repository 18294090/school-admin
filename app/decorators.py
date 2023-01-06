from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission
def permission_required(permisson):
    def decorate(f):
        @wraps(f)
        def decorated_fuction(*args, **kwargs):
            if not current_user.can(permisson):
                abort(403)
            return f(*args, **kwargs)
        return(decorated_fuction)
    return decorate

def admin_required(f):
    return permission_required(Permission.admin)(f)