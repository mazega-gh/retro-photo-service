import logging
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, viewsets
from rest_framework import generics
from .serializers import UserSerializer, RoleSerializer, GroupSerializer
from .models import Role
from django.shortcuts import render
from django.contrib.auth.models import Group as DjangoGroup

from django.contrib.auth import get_user_model
User = get_user_model()

logger = logging.getLogger('django')


class CurrentUserView(APIView):
    """Получить данные текущего пользователя (только авторизованным)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email,
            'id': user.id,
            'role': user.role.name if user.role else None,
            'is_admin': user.is_admin,
            'is_moderator': user.is_moderator,
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
    
@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """
    Регистрация нового пользователя (без CSRF).
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password2 = request.data.get('password2')

        if not username or not email or not password:
            return Response(
                {'error': 'Все поля обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if password != password2:
            return Response(
                {'error': 'Пароли не совпадают'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Пользователь с таким логином уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Пользователь с таким email уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаём пользователя с ролью "user"
        from .models import Role
        try:
            user_role = Role.objects.get(name='user')
        except Role.DoesNotExist:
            user_role = Role.objects.create(name='user')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.role = user_role
        user.save()

        # Автоматически авторизуем после регистрации
        login(request, user)

        logger.info(f"REGISTER SUCCESS: {username}")
        return Response({
            'username': user.username,
            'email': user.email,
            'id': user.id,
        }, status=status.HTTP_201_CREATED)
    

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_admin

class AdminPageView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        return render(request, 'admin_panel.html')  # нужен импорт render

class AdminUserListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = None 

class AdminUserUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Разрешённые поля для обновления
        updatable_fields = ['username', 'email', 'role_id']
        data = {k: v for k, v in request.data.items() if k in updatable_fields}
        
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'role_id' in data:
            try:
                role = Role.objects.get(pk=data['role_id'])
                user.role = role
            except Role.DoesNotExist:
                return Response({'error': 'Роль не найдена'}, status=400)
        
        user.save()  # вызовет наш кастомный save(), обновит права суперпользователя при смене роли
        serializer = self.get_serializer(user)
        return Response(serializer.data)

class AdminUserDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()

class RoleListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class AdminGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = DjangoGroup.objects.all()
    serializer_class = GroupSerializer