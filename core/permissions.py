from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    작성자에게만 수정 및 삭제 권한을 부여하고,
    나머지 사용자는 읽기 권한만 부여
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author.user == request.user
