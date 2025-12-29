from django.utils import timezone
from datetime import timedelta  # <--- IMPORTANTE: Agrega esto
from .models import Tarea

def notificaciones_globales(request):
    if not request.user.is_authenticated:
        return {'mis_notificaciones': [], 'conteo_notificaciones': 0}

    ahora = timezone.now()
    # Definimos el límite: "Ahora + 24 horas"
    mañana = ahora + timedelta(hours=24)
    
    notificaciones = Tarea.objects.filter(
        usuario=request.user,
        fecha_completado__isnull=True,    # Que no esté lista
        recordatorio_activo=True,         # Que tenga alarma activada
        
        # CAMBIO CLAVE:
        # Buscamos fechas que sean menores o iguales a "mañana"
        # Esto incluye: Lo que venció ayer (pasado) Y lo que vence hoy (futuro cercano)
        fecha_recordatorio__lte=mañana    
        
    ).order_by('fecha_recordatorio') # Ordenamos: primero lo más urgente

    return {
        'mis_notificaciones': notificaciones,
        'conteo_notificaciones': notificaciones.count()
    }