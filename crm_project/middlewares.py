from django.http import HttpResponseForbidden
from django.core.exceptions import DisallowedHost

class HostHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Попытка получения хоста, как это делает Django по умолчанию
            request.get_host()
        except DisallowedHost:
            # Если хост недопустимый, возвращаем 403
            return HttpResponseForbidden("Forbidden: Invalid host")
        
        # Если все ок, продолжаем обработку запроса
        response = self.get_response(request)
        return response
