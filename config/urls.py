# config/urls.py
from django.contrib import admin
from accounts.views import CurrentUserView, LoginView, LogoutView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from photos.views import RetroPhotoViewSet
from locations.views import LocationViewSet
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


router = DefaultRouter()
router.register(r'photos', RetroPhotoViewSet, basename='photo')
router.register(r'locations', LocationViewSet, basename='location')

urlpatterns = [
    path('', ensure_csrf_cookie(TemplateView.as_view(template_name='index.html')), name='home'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/login/', LoginView.as_view(), name='api-login'),
    path('api/logout/', LogoutView.as_view(), name='api-logout'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/user/', CurrentUserView.as_view()),
]

# Раздача медиа-файлов в разработке
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

