from django.db import models
from django.contrib.auth.models import User

# 1. Usuarios Externos
class UsuarioSistema(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.rut}"


# 2. Zonas
class Zona(models.Model):
    TIPO_ZONA = (
        ('segura', 'Segura'),
        ('publica', 'Pública'),
    )

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo_zona = models.CharField(max_length=10, choices=TIPO_ZONA, default='publica')

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_zona_display()})"


# 3. Permisos por zona
class PermisoZona(models.Model):
    usuario = models.ForeignKey(UsuarioSistema, on_delete=models.CASCADE, related_name='permisos')
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE, related_name='permisos')
    acceso_habilitado = models.BooleanField(default=True)

    class Meta:
        unique_together = ('usuario', 'zona')

    def __str__(self):
        return f"{self.usuario} -> {self.zona} ({'Habilitado' if self.acceso_habilitado else 'Denegado'})"


# 4. Registros de ingreso
class RegistroIngreso(models.Model):
    usuario_sistema = models.ForeignKey(UsuarioSistema, on_delete=models.SET_NULL, null=True, related_name='ingresos')
    zona = models.ForeignKey(Zona, on_delete=models.SET_NULL, null=True, related_name='ingresos')
    operador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    autorizado = models.BooleanField(default=False)
    comentario = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"Ingreso de {self.usuario_sistema} a {self.zona} ({'Autorizado' if self.autorizado else 'Denegado'})"


# 5. Imágenes de ingreso
class ImagenRegistro(models.Model):
    ingreso = models.ForeignKey(RegistroIngreso, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='ingresos/')

    def __str__(self):
        return f"Imagen de ingreso {self.ingreso}"
    



    # ==========================================================
# 6. Gestión de Vehículos y GPS
# ==========================================================

# Conductor
class Conductor(models.Model):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    licencia = models.CharField(max_length=20, null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.rut}"


# GPS
class GPS(models.Model):
    codigo_gps = models.CharField(max_length=50, unique=True)
    coordenada_lat = models.FloatField(null=True, blank=True)
    coordenada_long = models.FloatField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GPS {self.codigo_gps}"


# Vehículo
class Vehiculo(models.Model):
    patente = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField()
    color = models.CharField(max_length=30, null=True, blank=True)
    activo = models.BooleanField(default=True)
    conductor = models.ForeignKey(Conductor, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos')
    gps = models.OneToOneField(GPS, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculo')

    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"


# Historial de ubicaciones
class HistorialUbicacion(models.Model):
    gps = models.ForeignKey(GPS, on_delete=models.CASCADE, related_name='historial')
    latitud = models.FloatField()
    longitud = models.FloatField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Historial {self.gps.codigo_gps} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

