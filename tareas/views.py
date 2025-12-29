import random
import csv
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import update_session_auth_hash # <--- IMPORTANTE PARA NO DESLOGUEAR

# --- TUS MODELOS ---
from .models import Tarea, Categoria, Perfil, SubTarea, Nota, Movimiento

# --- TUS FORMULARIOS ---
from .forms import (
    TareaForm,
    RegistroUsuarioForm,
    SolicitarRecuperacionForm,
    NuevaContrasenaForm,
    EditarPerfilForm,
    CustomPasswordChangeForm  # <--- AHORA SÍ ESTÁ BIEN IMPORTADO
)
def landing_page(request):
    # Si el usuario YA está logueado, lo mandamos directo a sus tareas
    if request.user.is_authenticated:
        return redirect('home')
    
    # Si es un visitante anónimo, le mostramos la Landing Page
    return render(request, 'landing.html')
# ==========================================
#              VISTAS PRINCIPALES
# ==========================================

@login_required 
def home(request):
    # 1. TAREAS (Buscador y Listado)
    tareas = Tarea.objects.filter(usuario=request.user).order_by('-creado')
    
    query = request.GET.get('buscador')
    if query:
        tareas = tareas.filter(titulo__icontains=query)

    # 2. DATOS PARA EL DASHBOARD
    # Contadores
    total_tareas = tareas.count()
    pendientes = tareas.filter(completada=False).count()
    completadas = total_tareas - pendientes
    
    # Calcular porcentaje de victoria (para barra de progreso)
    porcentaje_completado = 0
    if total_tareas > 0:
        porcentaje_completado = int((completadas / total_tareas) * 100)

    # 3. BILLETERA (Saldo Rápido)
    movimientos = Movimiento.objects.filter(usuario=request.user)
    ingresos = movimientos.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    gastos = movimientos.filter(tipo='GASTO').aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_actual = ingresos - gastos

    # 4. NOTAS
    total_notas = Nota.objects.filter(usuario=request.user).count()

    return render(request, 'home.html', {
        'tareas': tareas,               # La lista completa (para mostrar abajo)
        'search_query': query,
        
        # Datos nuevos para las tarjetas
        'pendientes': pendientes,
        'saldo': saldo_actual,
        'porcentaje': porcentaje_completado,
        'total_notas': total_notas,
        
        # XP del usuario (para mostrar nivel en el home)
        'nivel': request.user.perfil.nivel,
        'xp': request.user.perfil.xp_siguiente_nivel
    })

@login_required
def crear_tarea(request):
    if request.method == 'GET':
        categorias = Categoria.objects.filter(usuario=request.user) | Categoria.objects.filter(usuario__isnull=True)
        return render(request, 'crear_tarea.html', {
            'form': TareaForm(),
            'categorias': categorias
        })
    else:
        try:
            form = TareaForm(request.POST)
            nuevo_todo = form.save(commit=False)
            nuevo_todo.usuario = request.user

            # --- LÓGICA DE CATEGORÍAS ---
            nueva_cat_nombre = request.POST.get('nueva_categoria')
            cat_existente_id = request.POST.get('categoria_existente')

            if nueva_cat_nombre:
                colores = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'dark']
                nueva_cat = Categoria.objects.create(
                    nombre=nueva_cat_nombre,
                    usuario=request.user,
                    color=random.choice(colores)
                )
                nuevo_todo.categoria = nueva_cat
            elif cat_existente_id:
                categoria = Categoria.objects.get(id=cat_existente_id)
                nuevo_todo.categoria = categoria

            nuevo_todo.save()
            return redirect('home')

        except ValueError:
            return render(request, 'crear_tarea.html', {
                'form': TareaForm(),
                'error': 'Por favor verifica los datos'
            })

@login_required
def detalle_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id, usuario=request.user)

    total_subtareas = tarea.subtareas.count()
    completadas = tarea.subtareas.filter(completado=True).count()

    progreso = 0
    if total_subtareas > 0:
        progreso = int((completadas / total_subtareas) * 100)

    return render(request, 'detalle_tarea.html', {
        'tarea': tarea,
        'progreso': progreso
    })

@login_required
def completar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id, usuario=request.user)
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)
    
    # Mapa de recompensas base
    XP_POR_DIFICULTAD = {
        'facil': 10,
        'media': 20,
        'dificil': 50
    }
    
    xp_base = XP_POR_DIFICULTAD.get(tarea.dificultad, 10)

    if request.method == 'POST':
        # CASO 1: MARCAR COMO COMPLETADA (SUMAR XP)
        if not tarea.completada:
            tarea.completada = True
            tarea.fecha_completado = timezone.now()
            
            # --- LÓGICA DE BONUS (Igual que antes) ---
            puntos_ganados = xp_base
            es_bonus = False

            if tarea.dificultad != 'facil':
                hoy = timezone.now().date()
                conteo_hoy = Tarea.objects.filter(
                    usuario=request.user,
                    completada=True,
                    dificultad=tarea.dificultad,
                    fecha_completado__date=hoy
                ).exclude(id=tarea.id).count()

                limite = 5 if tarea.dificultad == 'media' else 3
                
                if conteo_hoy >= limite:
                    puntos_ganados = 10 
                    messages.warning(request, f"Límite diario '{tarea.dificultad}' lleno. Solo ganaste XP base.")
                else:
                    es_bonus = True

            # Sumar al perfil
            perfil.puntos += puntos_ganados
            perfil.tareas_completadas_total += 1
            
            # Verificar subida de nivel
            if perfil.puntos >= 100:
                perfil.nivel += 1
                perfil.puntos -= 100 
                messages.success(request, f"¡NIVEL {perfil.nivel}! 🎉 (+{puntos_ganados} XP)")
            else:
                messages.success(request, f"¡Hecho! +{puntos_ganados} XP")

        # CASO 2: DESMARCAR / REABRIR (RESTAR XP)
        else:
            tarea.completada = False
            tarea.fecha_completado = None
            
            # Restamos los puntos para evitar trampas
            # (Restamos la base para no complicar el cálculo de bonus históricos)
            perfil.puntos -= xp_base
            perfil.tareas_completadas_total -= 1
            
            # Evitar que los puntos sean negativos
            if perfil.puntos < 0:
                perfil.puntos = 0
                
            messages.info(request, f"Tarea reabierta. Se han descontado {xp_base} XP.")

        # Guardamos ambos cambios
        tarea.save()
        perfil.save()
        
    return redirect('home')

    
@login_required
def eliminar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    if tarea.usuario == request.user:
        tarea.delete()
    return redirect('home')

@login_required
def editar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id, usuario=request.user)

    if request.method == 'POST':
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = TareaForm(instance=tarea)

    return render(request, 'editar_tarea.html', {
        'form': form,
        'tarea': tarea
    })

# ==========================================
#              USUARIOS & AUTH
# ==========================================

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': RegistroUsuarioForm()})
    else:
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            user.email = email
            user.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'signup.html', {
                'form': form,
                'error': 'Error en el registro. Revisa los datos.'
            })

def signin(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    else:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'signin.html', {
                'form': form,
                'error': 'Usuario o contraseña incorrectos'
            })

def signout(request):
    logout(request)
    return redirect('signin')

# --- RECUPERACIÓN DE CONTRASEÑA ---

def solicitar_recuperacion(request):
    if request.method == 'POST':
        form = SolicitarRecuperacionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                link = request.build_absolute_uri(f'/recuperar/{uid}/{token}/')

                send_mail(
                    "Recuperar contraseña - TaskMaster",
                    f"Hola {user.username},\n\nCambia tu contraseña aquí:\n\n{link}",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
            return render(request, 'recuperacion_enviada.html')
    else:
        form = SolicitarRecuperacionForm()
    return render(request, 'solicitar_recuperacion.html', {'form': form})

def confirmar_recuperacion(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = NuevaContrasenaForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password'])
                user.save()
                return redirect('signin')
        else:
            form = NuevaContrasenaForm()
        return render(request, 'confirmar_recuperacion.html', {'form': form})
    else:
        return render(request, 'link_invalido.html')

# ==========================================
#              PERFIL GAMER
# ==========================================
@login_required
def perfil_usuario(request):
    perfil, created = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        # Pasamos request.FILES para poder recibir la imagen
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            # 1. Guardar la foto en el Perfil
            form.save()
            
            # 2. Guardar Nombre y Apellido en el Usuario
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            
            messages.success(request, "¡Perfil actualizado con éxito!")
            return redirect('perfil')
    else:
        # Pre-llenamos el formulario con los datos actuales
        form = EditarPerfilForm(instance=perfil, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name
        })

    # Lógica de progreso y foto de Google (la que ya tenías)
    progreso = perfil.xp_siguiente_nivel
    faltan = 100 - progreso
    
    avatar_url = None
    
    # PRIORIDAD DE FOTO: 
    # 1. Si el usuario subió una foto manual, usar esa.
    if perfil.avatar:
        avatar_url = perfil.avatar.url
    # 2. Si no, intentar buscar la de Google.
    else:
        try:
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            avatar_url = social_account.extra_data.get('picture')
        except SocialAccount.DoesNotExist:
            avatar_url = None

    return render(request, 'perfil.html', {
        'progreso': progreso,
        'faltan': faltan,
        'avatar_url': avatar_url,
        'form': form  # <--- Enviamos el formulario al HTML
    })

# ==========================================
#              CALENDARIO
# ==========================================

@login_required
def vista_calendario(request):
    return render(request, 'calendario.html')

@login_required
def api_tareas_calendario(request):
    tareas = Tarea.objects.filter(usuario=request.user, fecha_recordatorio__isnull=False)
    eventos = []
    for tarea in tareas:
        color = '#0d6efd'
        if tarea.fecha_completado: color = '#198754'
        elif tarea.importante: color = '#dc3545'

        eventos.append({
            'title': tarea.titulo,
            'start': tarea.fecha_recordatorio.isoformat(),
            'url': f'/tarea/{tarea.id}/',
            'color': color
        })
    return JsonResponse(eventos, safe=False)

# ==========================================
#              SUBTAREAS
# ==========================================

@login_required
def agregar_subtarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id, usuario=request.user)
    if request.method == 'POST':
        titulo = request.POST.get('titulo_subtarea')
        if titulo:
            SubTarea.objects.create(tarea=tarea, titulo=titulo)
    return redirect('detalle_tarea', tarea_id=tarea.id)

@login_required
def eliminar_subtarea(request, id_subtarea):
    subtarea = get_object_or_404(SubTarea, pk=id_subtarea)
    if subtarea.tarea.usuario == request.user:
        tarea_id = subtarea.tarea.id
        subtarea.delete()
        return redirect('detalle_tarea', tarea_id=tarea_id)
    return redirect('home')

@login_required
def cambiar_estado_subtarea(request, id_subtarea):
    subtarea = get_object_or_404(SubTarea, pk=id_subtarea)
    if subtarea.tarea.usuario == request.user:
        subtarea.completado = not subtarea.completado
        subtarea.save()
        return redirect('detalle_tarea', tarea_id=subtarea.tarea.id)
    return redirect('home')

# ==========================================
#              NOTAS (APUNTES)
# ==========================================

@login_required
def notas(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        contenido = request.POST.get('contenido')
        color = request.POST.get('color', 'bg-warning') # Amarillo por defecto
        
        if contenido:
            Nota.objects.create(
                usuario=request.user,
                titulo=titulo,
                contenido=contenido,
                color=color
            )
            messages.success(request, "¡Nota pegada en el tablero!")
            return redirect('notas')

    # Traemos todas las notas del usuario ordenadas por las más nuevas
    mis_notas = Nota.objects.filter(usuario=request.user).order_by('-destacada', '-actualizado')
    
    return render(request, 'notas.html', {'notas': mis_notas})

@login_required
def eliminar_nota(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id, usuario=request.user)
    nota.delete()
    messages.success(request, "Nota arrancada y tirada a la basura 🗑️")
    return redirect('notas')

# ==========================================
#         PRESUPUESTO (BILLETERA)
# ==========================================

@login_required
def ver_presupuesto(request):
    movimientos = Movimiento.objects.filter(usuario=request.user).order_by('-fecha')

    # Calcular Totales de forma segura
    sum_ingresos = movimientos.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum']
    total_ingresos = sum_ingresos if sum_ingresos else 0

    sum_gastos = movimientos.filter(tipo='GASTO').aggregate(Sum('monto'))['monto__sum']
    total_gastos = sum_gastos if sum_gastos else 0

    balance = total_ingresos - total_gastos

    return render(request, 'presupuesto.html', {
        'movimientos': movimientos,
        'ingresos': total_ingresos,
        'gastos': total_gastos,
        'balance': balance
    })

@login_required
def agregar_movimiento(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        monto = request.POST.get('monto')
        tipo = request.POST.get('tipo')

        if titulo and monto and tipo:
            Movimiento.objects.create(
                usuario=request.user,
                titulo=titulo,
                monto=monto,
                tipo=tipo
            )
    return redirect('presupuesto')

@login_required
def eliminar_movimiento(request, id_mov):
    mov = get_object_or_404(Movimiento, pk=id_mov, usuario=request.user)
    mov.delete()
    return redirect('presupuesto')

@login_required
def exportar_presupuesto(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mi_presupuesto.csv"'

    writer = csv.writer(response)
    writer.writerow(['Fecha', 'Título', 'Tipo', 'Monto'])

    movimientos = Movimiento.objects.filter(usuario=request.user).order_by('-fecha')
    for mov in movimientos:
        writer.writerow([mov.fecha, mov.titulo, mov.get_tipo_display(), mov.monto])

    return response
@login_required
def fijar_nota(request, nota_id):
    nota = get_object_or_404(Nota, pk=nota_id, usuario=request.user)
    # Interruptor: Si es True pasa a False, y viceversa
    nota.destacada = not nota.destacada 
    nota.save()
    return redirect('notas')

@login_required
def ranking(request):
    # Traemos los perfiles ordenados por Nivel (desc) y luego Puntos (desc)
    # select_related('usuario') optimiza la consulta para no hacer 100 llamadas a la DB
    jugadores = Perfil.objects.select_related('usuario').order_by('-nivel', '-puntos')
    
    return render(request, 'ranking.html', {'jugadores': jugadores})




@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Esta línea es CLAVE: Mantiene la sesión iniciada después del cambio
            update_session_auth_hash(request, user) 
            messages.success(request, '¡Tu contraseña ha sido actualizada correctamente! 🔒')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores abajo.')
    else:
        form = CustomPasswordChangeForm(request.user)
        
    return render(request, 'cambiar_contrasena.html', {
        'form': form
    })
    
@login_required
def api_terminar_pomodoro(request, tarea_id):
    if request.method == 'POST':
        # Busamos la tarea y el perfil
        tarea = get_object_or_404(Tarea, pk=tarea_id, usuario=request.user)
        perfil, created = Perfil.objects.get_or_create(usuario=request.user)
        
        # RECOMPENSA: 50 XP por 25 minutos de enfoque puro
        puntos_ganados = 50
        perfil.puntos += puntos_ganados
        
        # Verificar si sube de nivel
        subio_nivel = False
        if perfil.puntos >= 100:
            perfil.nivel += 1
            perfil.puntos -= 100
            subio_nivel = True
            
        perfil.save()
        
        return JsonResponse({
            'status': 'success', 
            'puntos': puntos_ganados,
            'nuevo_total': perfil.puntos,
            'subio_nivel': subio_nivel,
            'nuevo_nivel': perfil.nivel
        })
    return JsonResponse({'status': 'error'}, status=400)
