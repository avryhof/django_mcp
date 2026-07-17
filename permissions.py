from django.conf import settings


class MCPPermission:

    def has_permission(self, request, tool):
        return True

    def __call__(self, request, tool):
        return self.has_permission(request, tool)


class IsAuthenticated(MCPPermission):

    def has_permission(self, request, tool):
        return request.user.is_authenticated


class IsAnonymous(MCPPermission):

    def has_permission(self, request, tool):
        return not request.user.is_authenticated


class AllowAny(MCPPermission):

    def has_permission(self, request, tool):
        return True


class DenyAll(MCPPermission):

    def has_permission(self, request, tool):
        return False


class DjangoPermission(MCPPermission):

    def __init__(self, permission_string):
        self.permission_string = permission_string
        self.app_label, self.codename = permission_string.split(".")

    def has_permission(self, request, tool):
        if not request.user.is_authenticated:
            return False
        return request.user.has_perm(self.permission_string)


class IsInGroup(MCPPermission):

    def __init__(self, group_name):
        self.group_name = group_name

    def has_permission(self, request, tool):
        if not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name=self.group_name).exists()


class IsSuperUser(MCPPermission):

    def has_permission(self, request, tool):
        return request.user.is_authenticated and request.user.is_superuser


class IsStaff(MCPPermission):

    def has_permission(self, request, tool):
        return request.user.is_authenticated and request.user.is_staff
