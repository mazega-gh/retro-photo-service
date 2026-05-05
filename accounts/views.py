import logging
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

logger = logging.getLogger('django')


class CurrentUserView(APIView):
    """Получить данные текущего пользователя (только авторизованным)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'id': request.user.id,
        })


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    Вход в систему.
    Никакой проверки CSRF, никакой сессионной аутентификации внутри DRF.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Сначала логируем сырые данные запроса
        logger.info(f"LOGIN RAW BODY: {request.body}")
        logger.info(f"LOGIN CONTENT TYPE: {request.content_type}")

        # Потом извлекаем переменные
        username = request.data.get('username')
        password = request.data.get('password')

        logger.info(f"LOGIN ATTEMPT: username={username}")

        if not username or not password:
            return Response(
                {'error': 'Укажите логин и пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            logger.info(f"LOGIN SUCCESS: {username}")
            return Response({
                'username': user.username,
                'email': user.email,
                'id': user.id,
            })
        else:
            logger.warning(f"LOGIN FAILED: {username}")
            return Response(
                {'error': 'Неверный логин или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """Выход из системы"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        logout(request)
        return Response({'detail': 'Вы вышли из системы'})