# config/urls.py
from django.contrib import admin as django_admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from photos.views import RetroPhotoViewSet, AdminRetroPhotoViewSet
from locations.views import (
    LocationViewSet, AdminLocationViewSet, AdminLocationTypeViewSet,
    AdminLocationTypeListView, CheckLocationView,
    ModerationLocationsAPIView, ApproveLocationAPIView, RejectLocationAPIView
)
from moderation.views import (
    moderation_page, ModerationPhotosAPIView, ApprovePhotoAPIView, RejectPhotoAPIView, ModerationLogAPIView,
    AdminModerationStatusViewSet, AdminModerationLogViewSet
)
from accounts.views import (
    CurrentUserView, LoginView, LogoutView, RegisterView,
    AdminPageView, AdminUserListAPIView, AdminUserUpdateAPIView, AdminUserDeleteAPIView,
    RoleListAPIView, AdminGroupViewSet
)

router = DefaultRouter()
router.register(r'photos', RetroPhotoViewSet, basename='photo')
router.register(r'locations', LocationViewSet, basename='location')
# Административные API-роуты
admin_router = DefaultRouter()
admin_router.register(r'admin/photos', AdminRetroPhotoViewSet, basename='admin-photo')
admin_router.register(r'admin/locations', AdminLocationViewSet, basename='admin-location')
admin_router.register(r'admin/location-types', AdminLocationTypeViewSet, basename='admin-location-type')
admin_router.register(r'admin/moderation-statuses', AdminModerationStatusViewSet, basename='admin-moderation-status')
admin_router.register(r'admin/moderation-logs', AdminModerationLogViewSet, basename='admin-moderation-log')
admin_router.register(r'admin/groups', AdminGroupViewSet, basename='admin-group')

urlpatterns = [
    path('', ensure_csrf_cookie(TemplateView.as_view(template_name='index.html')), name='home'),
    path('admin/', django_admin.site.urls),
    path('admin-panel/', AdminPageView.as_view(), name='admin-panel'),
    path('api/locations/check/', CheckLocationView.as_view(), name='location-check'),
    path('api/admin/users/', AdminUserListAPIView.as_view(), name='admin-user-list'),
    path('api/admin/users/<int:pk>/', AdminUserUpdateAPIView.as_view(), name='admin-user-update'),
    path('api/admin/roles/', RoleListAPIView.as_view(), name='admin-role-list'),
    path('moderation/', moderation_page, name='moderation-page'),
    path('api/moderation/photos/', ModerationPhotosAPIView.as_view(), name='moderation-photos'),
    path('api/moderation/photos/<int:pk>/approve/', ApprovePhotoAPIView.as_view(), name='approve-photo'),
    path('api/moderation/photos/<int:pk>/reject/', RejectPhotoAPIView.as_view(), name='reject-photo'),
    path('api/moderation/log/', ModerationLogAPIView.as_view(), name='moderation-log'),
    path('api/moderation/locations/', ModerationLocationsAPIView.as_view(), name='moderation-locations'),
    path('api/moderation/locations/<int:pk>/approve/', ApproveLocationAPIView.as_view(), name='approve-location'),
    path('api/moderation/locations/<int:pk>/reject/', RejectLocationAPIView.as_view(), name='reject-location'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/login/', LoginView.as_view(), name='api-login'),
    path('api/logout/', LogoutView.as_view(), name='api-logout'),
    path('api/register/', RegisterView.as_view(), name='api-register'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/user/', CurrentUserView.as_view()),
    path('api/', include(admin_router.urls)),
]

# Раздача медиа-файлов в разработке
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

