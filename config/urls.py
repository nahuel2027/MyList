from django.contrib import admin
from django.urls import path, include
from tareas import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. LA NUEVA PORTADA (Pública)
    # Al entrar a tuweb.com, verán la Landing Page
    path('', views.landing_page, name='landing'),

    # 2. EL DASHBOARD (Protegido)
    # Al loguearse, irán a tuweb.com/tablero/
    path('tablero/', views.home, name='home'),
    
    # --- RUTA PARA EL LOGIN DE GOOGLE ---
    path('accounts/', include('allauth.urls')),

    # --- RUTAS DE AUTENTICACIÓN ---
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),
    path('signin/', views.signin, name='signin'),
    
    # --- TAREAS ---
    path('crear/', views.crear_tarea, name='crear_tarea'),
    path('tarea/<int:tarea_id>/', views.detalle_tarea, name='detalle_tarea'),
    path('tarea/<int:tarea_id>/completar', views.completar_tarea, name='completar_tarea'),
    path('tarea/<int:tarea_id>/eliminar', views.eliminar_tarea, name='eliminar_tarea'),
    path('tarea/<int:tarea_id>/editar', views.editar_tarea, name='editar_tarea'),
    
    # --- RECUPERACIÓN DE CONTRASEÑA ---
    path('recuperar/', views.solicitar_recuperacion, name='solicitar_recuperacion'),
    path('recuperar/<uidb64>/<token>/', views.confirmar_recuperacion, name='confirmar_recuperacion'),
    
    # Rutas estándar de Django (opcionales pero útiles)
    path('reset_password/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # --- CALENDARIO Y SUBTAREAS ---
    path('calendario/', views.vista_calendario, name='calendario'),
    path('api/tareas/', views.api_tareas_calendario, name='api_tareas'),
    path('subtarea/<int:tarea_id>/agregar/', views.agregar_subtarea, name='agregar_subtarea'),
    path('subtarea/<int:id_subtarea>/cambiar/', views.cambiar_estado_subtarea, name='cambiar_estado_subtarea'),
    path('subtarea/<int:id_subtarea>/eliminar/', views.eliminar_subtarea, name='eliminar_subtarea'),
    
    # --- NOTAS ---
    path('notas/', views.notas, name='notas'),
    path('notas/eliminar/<int:nota_id>/', views.eliminar_nota, name='eliminar_nota'),
    path('notas/fijar/<int:nota_id>/', views.fijar_nota, name='fijar_nota'),
    
    # --- PRESUPUESTO ---
    path('presupuesto/', views.ver_presupuesto, name='presupuesto'),
    path('presupuesto/agregar/', views.agregar_movimiento, name='agregar_movimiento'),
    path('presupuesto/eliminar/<int:id_mov>/', views.eliminar_movimiento, name='eliminar_movimiento'),
    path('presupuesto/exportar/', views.exportar_presupuesto, name='exportar_presupuesto'),
    
    # --- PERFIL GAMER & EXTRAS ---
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('ranking/', views.ranking, name='ranking'),
    path('perfil/seguridad/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('api/pomodoro/<int:tarea_id>/', views.api_terminar_pomodoro, name='api_terminar_pomodoro'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)