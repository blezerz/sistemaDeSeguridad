"""
URL configuration for sistemaDeSeguridad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('baseOperador/', views.baseOperador, name='baseOperador'), 
    path('logout/', views.logout_view, name='logout'),
    path("carpAdmin/inicioAdmin/", views.inicioAdmin, name="inicioAdmin"),
    path("carpOperador/inicioOperador/", views.inicioOperador, name="inicioOperador"),
    path("inicioUsuarioBasico/", views.inicioUsuarioBasico, name="inicioUsuarioBasico"),
    path("buscar_usuario/", views.buscar_usuario, name="buscar_usuario"),
    path("transmision_camara/", views.transmision_camara, name="transmision_camara"),
    path("carpOperador/operadorRegistroAcceso/<int:zona_id>/", views.operadorRegistroAcceso, name="operadorRegistroAcceso"),
    path("registrar_ingreso/", views.registrar_ingreso, name="registrar_ingreso"),
    path("estado_rostro/", views.estado_rostro, name="estado_rostro"),
    path("carpAdmin/adminUsuario/", views.adminUsuario, name="adminUsuario"),
    path('editar_usuario_ajax/<int:usuario_id>/', views.editar_usuario_ajax, name='editar_usuario_ajax'),
    path('eliminarUsuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path("carpAdmin/usuario/<int:usuario_id>/", views.ver_usuario, name="ver_usuario"),
    path("crearUsuario/", views.crear_usuario, name="crear_usuario"),


    path('carpAdmin/zonas/', views.adminZonas, name='adminZonas'),
    path('carpAdmin/zonas/crear/', views.crear_zona, name='crear_zona'),
    path('carpAdmin/zonas/<int:zona_id>/', views.ver_zona, name='ver_zona'),
    path('carpAdmin/zonas/eliminar/<int:zona_id>/', views.eliminar_zona, name='eliminar_zona'),
    path('carpAdmin/zonas/cambiar_permiso/', views.cambiar_permiso_zona, name='cambiar_permiso_zona'),

    
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
