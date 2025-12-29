from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. MODELO CATEGORÍA
class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    OPCIONES_COLOR = [
        ('primary', 'Azul'),
        ('secondary', 'Gris'),
        ('success', 'Verde'),
        ('danger', 'Rojo'),
        ('warning', 'Amarillo'),
        ('info', 'Celeste'),
        ('dark', 'Negro')
    ]

    color = models.CharField(max_length=20, default='primary', choices=OPCIONES_COLOR)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.usuario:
            return f"{self.nombre} ({self.usuario.username})"
        return f"{self.nombre} (Global)"

# 2. MODELO TAREA
class Tarea(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    completada = models.BooleanField(default=False)
    
    # Fechas
    creado = models.DateTimeField(auto_now_add=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    importante = models.BooleanField(default=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    # Campos de recordatorio
    recordatorio_activo = models.BooleanField(default=False)
    fecha_recordatorio = models.DateTimeField(null=True, blank=True)
    
    # --- CAMPO NUEVO (Solo una vez) ---
    recordatorio_enviado = models.BooleanField(default=False) 

    # Conexión con Categoría
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
      
    # Dificultad (Gamificación)
    DIFICULTAD_OPCIONES = [
        ('facil', 'Fácil (+10 XP)'),
        ('media', 'Media (+20 XP)'),
        ('dificil', 'Difícil (+50 XP)'),
    ]

    dificultad = models.CharField(
        max_length=10, 
        choices=DIFICULTAD_OPCIONES, 
        default='facil'
    )
   
    def __str__(self):
        return self.titulo

# 3. MODELO PERFIL (Gamificación Unificado)
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    puntos = models.IntegerField(default=0)
    nivel = models.IntegerField(default=1)
    tareas_completadas_total = models.IntegerField(default=0)

    avatar = models.ImageField(upload_to='avatares/', blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username} - Nivel {self.nivel}"
    
    @property
    def xp_siguiente_nivel(self):
        return (self.puntos % 100)

# 4. MODELO SUBTAREA
class SubTarea(models.Model):
    tarea = models.ForeignKey(Tarea, related_name='subtareas', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    completado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

# 5. MODELO NOTA
class Nota(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, blank=True)
    contenido = models.TextField()
    color = models.CharField(max_length=20, default='bg-warning')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    destacada = models.BooleanField(default=False)

    def __str__(self):
        return f"Nota de {self.usuario}: {self.titulo}"

# 6. MODELO MOVIMIENTO (Presupuesto)
class Movimiento(models.Model):
    TIPOS = [
        ('INGRESO', 'Ingreso 💰'),
        ('GASTO', 'Gasto 💸')
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    fecha = models.DateField(default=timezone.now)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo}: {self.titulo} (${self.monto})"


# --- SEÑALES (SIGNALS) ---

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    Perfil.objects.get_or_create(usuario=instance)
    instance.perfil.save()