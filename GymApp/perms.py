from rest_framework import permissions

class CommentOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, review):
        return super().has_permission(request, view) and request.user == review.user