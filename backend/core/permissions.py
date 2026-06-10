from rest_framework.permissions import BasePermission


class IsInstanceOwner(BasePermission):
    message = "禁止進入"

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
