from django.conf import settings
from django.http import HttpResponseNotFound

ALLOWED_QUERY_KEY = "admin_key"
SESSION_FLAG = "admin_key_verified"


class HideAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path.startswith("/admin/"):
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)

            if request.session.get(SESSION_FLAG):
                return self.get_response(request)

            admin_key = getattr(settings, "ADMIN_ACCESS_KEY", "")
            if admin_key and request.GET.get(ALLOWED_QUERY_KEY) == admin_key:
                request.session[SESSION_FLAG] = True
                return self.get_response(request)

            return HttpResponseNotFound("<h1>PAGE NOT FOUND</h1>")

        return self.get_response(request)
