import threading


_context = threading.local()


def set_context(django_request=None):
    _context.django_request = django_request


def get_context():
    return getattr(_context, "django_request", None)


def clear_context():
    _context.django_request = None
