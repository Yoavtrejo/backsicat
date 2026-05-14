from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Proyecto
from .serializers import ProyectoSerializer


class ProyectoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para Proyectos.

    Endpoints generados automáticamente:
        GET    /api/proyectos/          → Listar todos
        POST   /api/proyectos/          → Crear nuevo
        GET    /api/proyectos/{id}/     → Detalle
        PUT    /api/proyectos/{id}/     → Actualizar completo
        PATCH  /api/proyectos/{id}/     → Actualizar parcial
        DELETE /api/proyectos/{id}/     → Eliminar
    """
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer

    def get_queryset(self):
        """Permite filtrar por estado, municipio y categoría via query params."""
        queryset = Proyecto.objects.all()

        estado = self.request.query_params.get('estado')
        municipio = self.request.query_params.get('municipio')
        categoria = self.request.query_params.get('categoria')
        anio = self.request.query_params.get('anio')

        if estado:
            queryset = queryset.filter(estado__icontains=estado)
        if municipio:
            queryset = queryset.filter(municipio__icontains=municipio)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if anio:
            queryset = queryset.filter(anio=anio)

        return queryset

    def perform_create(self, serializer):
        """Asigna automáticamente el usuario autenticado al crear un proyecto."""
        serializer.save(creado_por=self.request.user)
