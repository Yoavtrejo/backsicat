from rest_framework import generics, permissions, viewsets
from .serializers import UserSerializer
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle] 

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Si el correo está registrado, recibirás un enlace."}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

        try:
            html_message = f"""
                <h2>Recuperación de contraseña</h2>
                <p>Hola {user.username}, recibimos una solicitud de recuperación de contraseña para tu cuenta.</p>
                <p>Haz clic en el enlace para crear una contraseña nueva:</p>
                <a href="{reset_link}" style="display:inline-block; padding:10px 20px; background-color:#004b71; color:#fff; text-decoration:none; border-radius:5px;">Restablecer Contraseña</a>
                <p>Si no solicitaste este cambio, simplemente ignora este correo.</p>
            """
            send_mail(
                subject="Recuperación de Contraseña - SICAT",
                message="", 
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return Response({"message": "Si el correo está registrado, recibirás un enlace."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno enviando correo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        try:
            id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Contraseña actualizada exitosamente."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "El enlace es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        raw_password = self.request.data.get('password', '')
        user = serializer.save()

        if user.email:
            login_url = f"{settings.FRONTEND_URL}/login"
            html_message = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #173F4A, #1D7147); padding: 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Bienvenido a SICAT</h1>
                    <p style="color: #a8d5ba; margin-top: 8px; font-size: 14px;">Sistema de Información Catastral</p>
                </div>
                <div style="padding: 30px; background-color: #ffffff;">
                    <p style="color: #333; font-size: 16px;">Hola <strong>{user.first_name or user.username}</strong>,</p>
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        Se ha creado una cuenta para ti en la plataforma SICAT.
                        A continuación encontrarás tus credenciales de acceso:
                    </p>
                    <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #888; font-size: 13px; width: 140px;">Usuario:</td>
                                <td style="padding: 8px 0; color: #173F4A; font-size: 15px; font-weight: bold;">{user.username}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #888; font-size: 13px;">Contraseña:</td>
                                <td style="padding: 8px 0; color: #173F4A; font-size: 15px; font-weight: bold;">{raw_password}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #888; font-size: 13px;">Correo registrado:</td>
                                <td style="padding: 8px 0; color: #173F4A; font-size: 15px;">{user.email}</td>
                            </tr>
                        </table>
                    </div>
                    <div style="text-align: center; margin: 25px 0;">
                        <a href="{login_url}" style="display: inline-block; padding: 12px 30px; background-color: #1D7147; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px;">
                            Iniciar Sesión
                        </a>
                    </div>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Por seguridad, te recomendamos cambiar tu contraseña después de iniciar sesión por primera vez.
                    </p>
                </div>
            </div>
            """
            try:
                send_mail(
                    subject="Bienvenido a SICAT - Tus credenciales de acceso",
                    message=f"Hola {user.first_name or user.username}, tus credenciales de acceso a SICAT son: Usuario: {user.username} | Contraseña: {raw_password}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al enviar correo de bienvenida a {user.email}: {e}")