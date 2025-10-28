from django.http import HttpResponseNotFound

class HideAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and not (request.user.is_authenticated and request.user.is_superuser):
            return HttpResponseNotFound('<h1>You cant access this page</h1>')
        return self.get_response(request)
