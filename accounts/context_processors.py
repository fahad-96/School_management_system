from .helpers import get_children, get_current_student


def student_context(request):
    """Exposes the parent's children + currently selected child to every template."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_parent:
        return {}
    return {
        'children': get_children(user),
        'current_student': get_current_student(request),
    }
