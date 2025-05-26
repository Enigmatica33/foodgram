from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Разрешение: только для админов (включая staff/superuser)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение: только для админов на запись, остальным — только чтение."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_superuser


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Изменение объекта для автора, для остальных - только чтение."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAuthor(IsAuthorOrReadOnly):
    def has_obj_permission(self, request, view, obj):
        return obj.author == request.user
