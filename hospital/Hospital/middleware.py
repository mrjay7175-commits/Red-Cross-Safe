import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


class CurrentUserMiddleware:
    """
    Stashes the current request's user in a thread-local so that model
    signal handlers (which don't get the request) can attribute changes
    to the right user for the audit log.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)

        response = self.get_response(request)

        _thread_locals.user = None

        return response
