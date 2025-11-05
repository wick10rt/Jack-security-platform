from django.http import HttpResponseNotFound

class HideAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        referer = request.META.get('HTTP_REFERER', '')

        if path.startswith('/admin/') and not path.startswith('/admin/login/'):
            if not referer.startswith('http://localhost:5173'):
                if not (request.user.is_authenticated and request.user.is_staff):
                    return HttpResponseNotFound('<h1>you cant access this page</h1>')
        return self.get_response(request)


