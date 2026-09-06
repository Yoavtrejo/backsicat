from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from users.views import UserProfileView, PasswordResetRequestView, PasswordResetConfirmView, UserViewSet
from users.serializers import CustomTokenObtainPairSerializer
from upload_fields.views import SubirCapaNormalizadaView
from projects.views import ProyectoViewSet
from ai_assistant.views import ExplicarElementoView, GenerarInformeView

router = routers.DefaultRouter()
router.register('proyectos', ProyectoViewSet, basename='proyectos')
router.register('usuarios', UserViewSet, basename='usuarios')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/login/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/me/', UserProfileView.as_view(), name='user-profile'),
    path('api/subir-capa/', SubirCapaNormalizadaView.as_view(), name='subir-capa'),
    path('api/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('api/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/subir-capa/<int:pk>/', SubirCapaNormalizadaView.as_view(), name='subir-capa-detail'),
    path('api/ai/capa/explicar-elemento/', ExplicarElementoView.as_view(), name='ai-explicar-elemento'),
    path('api/ai/informes/generar/', GenerarInformeView.as_view(), name='ai-generar-informe'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
