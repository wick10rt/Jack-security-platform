from django.http import HttpResponseNotFound

ALLOWED_QUERY_KEY = "admin_key"
# 要跟frontend/.env → VITE_ADMIN_ACCESS_KEY 一樣
ALLOWED_QUERY_VALUE = "@1121717dogdog1101737fatfat"
SESSION_FLAG = "admin_key_verified"


# C-2
# 其他使用者不可以訪問管理員頁面
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

            if request.GET.get(ALLOWED_QUERY_KEY) == ALLOWED_QUERY_VALUE:
                request.session[SESSION_FLAG] = True
                return self.get_response(request)

            return HttpResponseNotFound("<h1>禁止進入!!!</h1>")

        return self.get_response(request)
