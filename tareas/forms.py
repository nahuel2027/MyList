from django.forms import ModelForm
from django import forms
from .models import Tarea, Perfil  # <--- CORRECCIÓN: Agregado 'Perfil' aquí
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm # <--- Agrega PasswordChangeForm
# --- FORMULARIO DE TAREA (UNIFICADO) ---
class TareaForm(ModelForm):
    class Meta:
        model = Tarea
        # 1. Aquí ponemos TODOS los campos juntos
        fields = ['titulo', 'descripcion', 'importante', 'recordatorio_activo', 'fecha_recordatorio', 'categoria', 'dificultad']
        
        # 2. Aquí definimos los estilos (Widgets) para que se vean bonitos con Bootstrap
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Comprar pan'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalles extra...'}),
            'fecha_recordatorio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            # Estilo especial para la dificultad
            'dificultad': forms.Select(attrs={'class': 'form-select fw-bold text-primary'}), 
        }

    # --- VALIDACIÓN DE FECHA ---
    def clean_fecha_recordatorio(self):
        fecha = self.cleaned_data.get('fecha_recordatorio')
        if fecha:
            if fecha < timezone.now():
                raise forms.ValidationError("¡No puedes programar un recordatorio en el pasado!")
        return fecha

# --- FORMULARIO DE REGISTRO ---
class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")

    class Meta:
        model = User
        fields = ['username', 'email']

# --- FORMULARIOS DE RECUPERACIÓN ---
class SolicitarRecuperacionForm(forms.Form):
    email = forms.EmailField(label="Correo Electrónico", required=True)

class NuevaContrasenaForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Nueva contraseña'}),
        label="Nueva Contraseña"
    )
    confirmar = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la contraseña'}),
        label="Confirmar Contraseña"
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirmar")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
# --- FORMULARIO DE EDICIÓN DE PERFIL ---
class EditarPerfilForm(forms.ModelForm):
    # Campos extra del modelo User (Nombre y Apellido)
    first_name = forms.CharField(max_length=30, required=False, label="Nombre")
    last_name = forms.CharField(max_length=30, required=False, label="Apellido")

    class Meta:
        model = Perfil
        fields = ['avatar'] # Del perfil solo queremos editar el avatar

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estilos Bootstrap para el input de archivo y textos
        self.fields['avatar'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        
        # --- FORMULARIO CAMBIO DE CONTRASEÑA ---
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ponerle estilo Bootstrap a todos los campos
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})