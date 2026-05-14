import logging

from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ExplicarElementoSerializer, GenerarInformeSerializer
from .services import build_report_context, explain_spatial_element, generate_report_text

logger = logging.getLogger(__name__)


class ExplicarElementoView(APIView):
    """
    POST /api/ai/capa/explicar-elemento/
    Body: { "nombre_capa"?, "categoria"?, "properties": { ... } }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ExplicarElementoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        nombre_capa = (ser.validated_data.get("nombre_capa") or "").strip() or None
        categoria = (ser.validated_data.get("categoria") or "").strip() or None
        properties = ser.validated_data["properties"]

        try:
            texto = explain_spatial_element(nombre_capa, categoria, properties)
        except RuntimeError as e:
            msg = str(e)
            if "Insufficient Balance" in msg or "(402)" in msg:
                return Response(
                    {
                        "detail": "El servicio de IA no está disponible por saldo insuficiente. "
                        "Recarga saldo en el proveedor o intenta más tarde."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            code = (
                status.HTTP_503_SERVICE_UNAVAILABLE
                if "No hay clave" in msg or "no está configurada" in msg
                else status.HTTP_502_BAD_GATEWAY
            )
            logger.warning("explicar-elemento: %s", msg)
            return Response({"detail": msg}, status=code)
        except RequestException as e:
            logger.exception("explicar-elemento: fallo de red")
            return Response(
                {"detail": f"No se pudo contactar al proveedor de IA: {e!s}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"explicacion": texto})


class GenerarInformeView(APIView):
    """
    POST /api/ai/informes/generar/
    Body: { estado?, municipio?, proyecto_id?, capa_ids?, tono? }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = GenerarInformeSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        data = ser.validated_data
        try:
            context = build_report_context(
                estado=(data.get("estado") or "").strip() or None,
                municipio=(data.get("municipio") or "").strip() or None,
                proyecto_id=data.get("proyecto_id"),
                capa_ids=data.get("capa_ids") or [],
            )
            informe = generate_report_text(context, data.get("tono", "ejecutivo"))
        except RuntimeError as e:
            msg = str(e)
            if "Insufficient Balance" in msg or "(402)" in msg:
                return Response(
                    {
                        "detail": "El servicio de IA no está disponible por saldo insuficiente. "
                        "Recarga saldo en el proveedor o intenta más tarde."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            code = (
                status.HTTP_503_SERVICE_UNAVAILABLE
                if "No hay clave" in msg or "no está configurada" in msg
                else status.HTTP_502_BAD_GATEWAY
            )
            logger.warning("generar-informe: %s", msg)
            return Response({"detail": msg}, status=code)
        except RequestException as e:
            logger.exception("generar-informe: fallo de red")
            return Response(
                {"detail": f"No se pudo contactar al proveedor de IA: {e!s}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"informe": informe, "contexto": context})
