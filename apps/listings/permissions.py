from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Читать могут все (если нужно)
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Изменять/удалять только владелец
        return obj.seller == request.user