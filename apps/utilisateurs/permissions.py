from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import Group


class IsAdminOrReadOnly(BasePermission):
    """Allow read-only access to everyone, write access to staff/admin only."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsProprietaireProfil(BasePermission):
    """Allow access if the requesting user owns the profile or is staff."""

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True
        # Expect obj to be a ProfilUtilisateur with a FK 'utilisateur'
        utilisateur = getattr(obj, 'utilisateur', None)
        return bool(utilisateur and utilisateur == request.user)


class HasRole(BasePermission):
    """Vérifie si l'utilisateur possède un des rôles requis."""

    required_roles: tuple[str, ...] = tuple()

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff:
            return True
        if not self.required_roles:
            return True
        user_groups = set(request.user.groups.values_list('name', flat=True))
        return any(role in user_groups for role in self.required_roles)


class IsAdminOrModerator(HasRole):
    required_roles = ("admin", "moderateur")


class IsSuperUser(BasePermission):
    """Autorise uniquement les superutilisateurs (is_superuser=True)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
