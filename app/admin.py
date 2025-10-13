from django.contrib import admin
from .models import UsuarioSistema, Zona, PermisoZona, RegistroIngreso, ImagenRegistro

# =======================
# USUARIOS DEL SISTEMA
# =======================
@admin.register(UsuarioSistema)
class UsuarioSistemaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombres', 'apellidos', 'rut', 'telefono', 'activo')
    search_fields = ('nombres', 'apellidos', 'rut')
    list_filter = ('activo',)


# =======================
# ZONAS
# =======================
@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'tipo_zona', 'descripcion')
    search_fields = ('nombre',)
    list_filter = ('tipo_zona',)


# =======================
# PERMISOS POR ZONA
# =======================
@admin.register(PermisoZona)
class PermisoZonaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'zona', 'acceso_habilitado')
    list_filter = ('acceso_habilitado', 'zona')
    search_fields = ('usuario__nombres', 'usuario__apellidos', 'usuario__rut')


# =======================
# REGISTROS DE INGRESO
# =======================
@admin.register(RegistroIngreso)
class RegistroIngresoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario_sistema', 'zona', 'fecha_ingreso', 'autorizado', 'operador')
    list_filter = ('autorizado', 'zona', 'fecha_ingreso')
    search_fields = ('usuario_sistema__nombres', 'usuario_sistema__apellidos', 'usuario_sistema__rut')


# =======================
# IMÁGENES DE REGISTRO
# =======================
@admin.register(ImagenRegistro)
class ImagenRegistroAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingreso', 'imagen')
    search_fields = ('ingreso__usuario_sistema__nombres', 'ingreso__usuario_sistema__apellidos')
