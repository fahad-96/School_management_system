from academics.models import Student


def get_children(user):
    return Student.objects.filter(parent__user=user).select_related('user', 'school_class')


def get_current_student(request):
    """The Student a student/parent user is currently looking at (parents can switch via ?child=<id>)."""
    user = request.user
    if user.is_student:
        return getattr(user, 'student', None)
    if user.is_parent:
        children = list(get_children(user))
        if not children:
            return None
        wanted = request.GET.get('child') or request.session.get('child_id')
        for child in children:
            if str(child.pk) == str(wanted):
                request.session['child_id'] = child.pk
                return child
        request.session['child_id'] = children[0].pk
        return children[0]
    return None
