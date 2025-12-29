from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from tareas.models import Tarea
from datetime import timedelta

class Command(BaseCommand):
    help = 'Envía notificaciones para tareas que vencen en las próximas 24 HORAS.'

    def handle(self, *args, **kwargs):
        # 1. Obtenemos la hora actual
        ahora_utc = timezone.now()
        ahora_local = timezone.localtime(ahora_utc)
        
        # --- EL CAMBIO CLAVE ---
        # Antes mirábamos 2 horas. Ahora miramos 24 HORAS hacia adelante.
        # Esto asegura que si el script corre una vez al día, cubra todo el día.
        limite_utc = ahora_utc + timedelta(hours=24)
        
        self.stdout.write(self.style.WARNING(f"--- 📅 REVISIÓN DIARIA ({ahora_local.strftime('%d/%m %H:%M')}) ---"))
        self.stdout.write(f"Buscando tareas que venzan desde AHORA hasta mañana a esta hora.")

        # 2. Buscar tareas
        tareas = Tarea.objects.filter(
            recordatorio_activo=True,                  # Usuario quiere aviso
            fecha_recordatorio__range=(ahora_utc, limite_utc), # Vence en las próximas 24hs
            recordatorio_enviado=False,                # No se avisó antes
            fecha_completado__isnull=True              # No está lista
        )

        if not tareas.exists():
            self.stdout.write("✅ No hay tareas pendientes de aviso para las próximas 24hs.")
            return

        # 3. Enviar Correos
        enviados = 0
        errores = 0
        
        for tarea in tareas:
            # Si no hay mail, pasamos
            if not tarea.usuario.email:
                self.stdout.write(self.style.WARNING(f"⚠ Tarea '{tarea.titulo}' saltada: Usuario sin email."))
                continue

            # Preparamos datos visuales
            hora_vencimiento_local = timezone.localtime(tarea.fecha_recordatorio)
            
            # Calculamos cuánto falta (para el texto del correo)
            diferencia = tarea.fecha_recordatorio - ahora_utc
            horas_restantes = int(diferencia.total_seconds() / 3600)
            minutos_restantes = int((diferencia.total_seconds() % 3600) / 60)
            
            # Texto amigable: "Vence hoy a las..." o "Vence mañana a las..."
            dia_vencimiento = "HOY" if hora_vencimiento_local.date() == ahora_local.date() else "MAÑANA"

            self.stdout.write(f"📩 Enviando a {tarea.usuario.email} | Tarea: '{tarea.titulo}' ({dia_vencimiento} a las {hora_vencimiento_local.strftime('%H:%M')})...")

            try:
                asunto = f"⏰ Recordatorio: {tarea.titulo}"
                
                mensaje = (
                    f"Hola {tarea.usuario.username},\n\n"
                    f"Tienes una tarea pendiente para {dia_vencimiento}:\n\n"
                    f"📌 {tarea.titulo}\n"
                    f"🕒 Hora límite: {hora_vencimiento_local.strftime('%H:%M')}\n"
                    f"⏳ Tiempo restante: {horas_restantes} horas y {minutos_restantes} minutos.\n\n"
                    f"¡No lo dejes para el último momento!\n"
                    f"Tu Gestor de Tareas"
                )
                
                send_mail(
                    asunto, 
                    mensaje, 
                    settings.EMAIL_HOST_USER, 
                    [tarea.usuario.email],
                    fail_silently=False
                )
                
                # Marcar como enviado
                tarea.recordatorio_enviado = True
                tarea.save()
                enviados += 1
                self.stdout.write(self.style.SUCCESS("   ✅ ¡Enviado!"))

            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f"   ❌ Falló el envío: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- Fin. Enviados: {enviados} | Errores: {errores} ---"))