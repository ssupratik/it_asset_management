from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve

EXEMPT_URLS = [
    "login",  # name of your login URL
    "admin:login",
    "admin:logout",
]


class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to access any page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_url = resolve(request.path_info).url_name

        if not request.user.is_authenticated and current_url not in EXEMPT_URLS:
            return redirect(settings.LOGIN_URL)

        return self.get_response(request)
