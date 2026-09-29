from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

ADMIN = 'admin'
TEACHER = 'teacher'
STUDENT = 'student'
PARENT = 'parent'
STAFF = (ADMIN, TEACHER)
ALL = (ADMIN, TEACHER, STUDENT, PARENT)


def user_has_role(user, roles):
    return user.is_superuser or user.role in roles


def role_required(*roles):
    """Decorator: user must be logged in and have one of the given roles (superusers always pass)."""

    def decorator(view):
        @wraps(view)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not user_has_role(request.user, roles):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return _wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ALL

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not user_has_role(request.user, self.allowed_roles):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = (ADMIN,)


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = STAFF
