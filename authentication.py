class MCPAuthentication:

    def authenticate(self, request):
        return None

    def __call__(self, request):
        return self.authenticate(request)


class SessionAuthentication(MCPAuthentication):

    def authenticate(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None


class RemoteUserAuthentication(MCPAuthentication):

    header = "REMOTE_USER"

    def authenticate(self, request):
        remote_user = request.META.get(self.header)
        if remote_user:
            return remote_user
        return None
