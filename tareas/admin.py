from django.contrib import admin
from .models import Tarea,Categoria,Perfil

# Esto hace que la tabla Tarea aparezca en el panel
class TareaAdmin(admin.ModelAdmin):
    readonly_fields = ("creado", ) # Campos de solo lectura

admin.site.register(Tarea, TareaAdmin)
admin.site.register(Categoria)
admin.site.register(Perfil)