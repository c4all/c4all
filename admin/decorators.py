from django.http import HttpResponseBadRequest

from django.shortcuts import redirect


def admin_required(fn):
    """
    View decorator for checking if user is logged in and is member of staff.
    If not logged in, redirect to custom settings-defined login page.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect('c4all_admin:login_admin')
        return fn(request, *args, **kwargs)
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def ajax_required(f):
    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
