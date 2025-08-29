import threading

_local = threading.local()


def set_current_user(user):
    _local.user = user


def get_current_user():
    return getattr(_local, "user", None)


def clear_current_user():
    if hasattr(_local, "user"):
        del _local.user


class CurrentUserMiddleware:
    """
    Add to settings.MIDDLEWARE:
    'assets.current_user.CurrentUserMiddleware'
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # store user (may be AnonymousUser)
        set_current_user(getattr(request, "user", None))
        response = self.get_response(request)
        clear_current_user()
        return response
