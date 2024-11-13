from rest_framework import permissions
import redis
from django.contrib.auth.models import User, AnonymousUser
from lab1.settings import REDIS_HOST, REDIS_PORT
from rest_framework.exceptions import PermissionDenied

# Настройки подключения к Redis
session_storage = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)


def get_user_from_session(request):

    session_id = request.COOKIES.get('session_id')

    if session_id:
        # Проверяем наличие session_id в Redis
        username = session_storage.get(session_id)
        if username:
            username = username.decode('utf-8')  # Декодируем bytes в строку
            try:
                user = User.objects.get(username=username)
                return user
            except User.DoesNotExist:
                return None
    return None


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        user = get_user_from_session(request)
        if user:
            request.user = user
            return True

        request.user = AnonymousUser()
        return False


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        user = get_user_from_session(request)
        if user:
            request.user = user
            # Проверка, что пользователь staff и не является создателем заявки
            if user.is_staff and not user.is_superuser and not user == view.get_object().creator:
                return True
        request.user = AnonymousUser()
        return False



class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = get_user_from_session(request)
        if user:
            request.user = user
            if user.is_superuser:
                return True
            else:
                raise PermissionDenied("You do not have permission to perform this action.")
        request.user = AnonymousUser()
        return False


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):

        if request.method in permissions.SAFE_METHODS:
            return True

        user = get_user_from_session(request)

        if user:
            request.user = user
            return True

        return False