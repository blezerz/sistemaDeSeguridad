from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import Group
import cv2
from django.http import StreamingHttpResponse
from django.http import JsonResponse,StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UsuarioSistema, Zona, PermisoZona, RegistroIngreso, ImagenRegistro
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import base64
from django.core.paginator import Paginator
from django.core.files.base import ContentFile

from django.views.decorators.csrf import csrf_exempt
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
detectar_rostro = False
rostro_detectado = False
# Create your views here.


def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Superusuario
            if user.is_superuser:
                return redirect("/admin/")

            # Verificar grupos
            if user.groups.filter(name="Administrador").exists():
                return redirect("../carpAdmin/inicioAdmin/")
            elif user.groups.filter(name="Operador").exists():
                return redirect("../carpOperador/inicioOperador/")
            elif user.groups.filter(name="UsuarioBasico").exists():
                return redirect("../inicioUsuarioBasico")
            else:
                return redirect("/")  # fallback
        else:
            return render(request, "login.html", {"error": "Usuario o contraseña incorrectos"})

    return render(request, "login.html")





def logout_view(request):
    return redirect("../login")








def baseOperador(request):
    return render(request, "baseOperador.html")




def movimiento_boton_navegador(request, template, context=None):
    # ⚡ Estado inicial: siempre True (navegador visible al inicio)
    if "mostrar_menu" not in request.session:
        request.session["mostrar_menu"] = True

    mostrar_menu = request.session["mostrar_menu"]

    # ⚡ Solo alternar si llega toggle
    if "toggle" in request.GET:
        mostrar_menu = not mostrar_menu
        request.session["mostrar_menu"] = mostrar_menu
        return redirect(request.path)  # vuelve a la misma URL sin ?toggle

    # ⚡ Pasar el estado al contexto
    ctx = context or {}
    ctx["mostrar_menu"] = mostrar_menu
    return render(request, template, ctx)



def inicioAdmin(request):
    return movimiento_boton_navegador(request, "carpAdmin/inicioAdmin.html")



def inicioOperador(request):
    zonas_list = Zona.objects.all().order_by('id')  # Ordenar por ID o nombre si prefieres
    paginator = Paginator(zonas_list, 5)  # 👈 5 zonas por página

    page_number = request.GET.get('page')
    zonas = paginator.get_page(page_number)

    return movimiento_boton_navegador(request, "carpOperador/inicioOperador.html", {
        "zonas": zonas,
        "paginator": paginator,
    })

def operadorRegistroAcceso(request, zona_id):
    zona = Zona.objects.get(id=zona_id)
    return render(request, "carpOperador/operadorRegistroAcceso.html", {"zona": zona})


def inicioUsuarioBasico(request):
    return movimiento_boton_navegador(request, "inicioUsuarioBasico.html")



#camara

def generar_fotogramas():
    global detectar_rostro, rostro_detectado
    camara = cv2.VideoCapture(1)
    while True:
        exito, fotograma = camara.read()
        if not exito:
            break

        rostro_detectado = False  # por defecto en cada frame
        if detectar_rostro:
            gris = cv2.cvtColor(fotograma, cv2.COLOR_BGR2GRAY)
            rostros = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

            for (x, y, w, h) in rostros:
                cv2.rectangle(fotograma, (x, y), (x+w, y+h), (0, 255, 0), 3)
                rostro_detectado = True  # 👈 solo si detecta
                break

        ret, buffer = cv2.imencode('.jpg', fotograma)
        fotograma = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + fotograma + b'\r\n')

    camara.release()



def estado_rostro(request):
    """Devuelve si hay rostro detectado o no."""
    global rostro_detectado
    return JsonResponse({"rostro": rostro_detectado})



def transmision_camara(request):
    return StreamingHttpResponse(
        generar_fotogramas(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


def buscar_usuario(request):
    global detectar_rostro
    rut = request.GET.get("rut", "").strip()
    zona_id = request.GET.get("zona")

    if not rut or not zona_id:
        return JsonResponse({"error": "Debe ingresar un RUT y zona"}, status=400)

    try:
        usuario = UsuarioSistema.objects.get(rut=rut)
        # Verificar si el usuario tiene permiso en esa zona
        tiene_permiso = usuario.permisos.filter(zona_id=zona_id, acceso_habilitado=True).exists()

        detectar_rostro = tiene_permiso  # Solo activa detección si tiene permiso

        return JsonResponse({
            "usuario_id": usuario.id,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "telefono": usuario.telefono,
            "activo": usuario.activo,
            "permiso": tiene_permiso,
        })
    except UsuarioSistema.DoesNotExist:
        detectar_rostro = False
        return JsonResponse({"error": "Usuario no encontrado"}, status=404)
    



@csrf_exempt   # 👈 para permitir la llamada desde fetch (usa CSRF en prod con cuidado)
def registrar_ingreso(request):
    if request.method == "POST":
        usuario_id = request.POST.get("usuario_id")
        zona_id = request.POST.get("zona_id")
        autorizado = request.POST.get("autorizado") == "true"
        comentario = request.POST.get("comentario", "")
        imagen_base64 = request.POST.get("imagen")  # 👈 capturamos la imagen enviada

        try:
            usuario = UsuarioSistema.objects.get(id=usuario_id)
            zona = Zona.objects.get(id=zona_id)

            # Guardar el registro
            registro = RegistroIngreso.objects.create(
                usuario_sistema=usuario,
                zona=zona,
                operador=request.user,
                autorizado=autorizado,
                comentario=comentario
            )

            # Guardar la imagen asociada (si llega)
            if imagen_base64:
                formato, imgstr = imagen_base64.split(';base64,')
                ext = formato.split('/')[-1]  # ej: jpg o png
                archivo = ContentFile(base64.b64decode(imgstr), name=f"ingreso_{registro.id}.{ext}")

                ImagenRegistro.objects.create(
                    ingreso=registro,
                    imagen=archivo
                )

            return JsonResponse({"ok": True, "mensaje": "Registro con imagen guardado", "id": registro.id})

        except UsuarioSistema.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Usuario no encontrado"}, status=404)
        except Zona.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Zona no encontrada"}, status=404)

    return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)


def adminUsuario(request):
    return movimiento_boton_navegador(request, "carpAdmin/adminUsuario.html")



#adminsitrador

from django.db.models import Q

def adminUsuario(request):
    # Obtener búsqueda desde el GET
    query = request.GET.get("q", "").strip()
    usuarios_list = UsuarioSistema.objects.all().order_by('id')

    # Si hay texto en el buscador, filtramos
    if query:
        usuarios_list = usuarios_list.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(rut__icontains=query)
        )

    # Paginación
    paginator = Paginator(usuarios_list, 10)  # 10 por página
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    # Contexto
    context = {
        "usuarios": usuarios,
        "query": query,
        "mostrar_menu": request.session.get("mostrar_menu", True),
    }

    return movimiento_boton_navegador(request, "carpAdmin/adminUsuario.html", context)


from django.shortcuts import get_object_or_404
def ver_usuario(request, usuario_id):
    usuario = get_object_or_404(UsuarioSistema, id=usuario_id)

    return movimiento_boton_navegador(request, "carpAdmin/verUsuario.html", {
        "usuario": usuario,
        "mostrar_menu": request.session.get("mostrar_menu", True),
    })


from django.contrib import messages


def crear_usuario(request):
    if request.method == "POST":
        nombres = request.POST.get("nombres")
        apellidos = request.POST.get("apellidos")
        rut = request.POST.get("rut")
        telefono = request.POST.get("telefono")
        password = request.POST.get("password")
        activo = bool(request.POST.get("activo"))

        # Verificar si el usuario ya existe
        if UsuarioSistema.objects.filter(rut=rut).exists():
            messages.error(request, "El RUT ingresado ya está registrado.")
            return redirect("crear_usuario")

        # Crear el usuario del sistema
        nuevo_usuario = UsuarioSistema.objects.create(
            nombres=nombres,
            apellidos=apellidos,
            rut=rut,
            telefono=telefono,
            activo=activo,
        )

        # 🔹 Crear permisos automáticos para todas las zonas
        zonas = Zona.objects.all()
        permisos_a_crear = []

        for zona in zonas:
            # Si la zona es pública → acceso habilitado
            acceso = True if zona.tipo_zona == "publica" else False
            permisos_a_crear.append(
                PermisoZona(usuario=nuevo_usuario, zona=zona, acceso_habilitado=acceso)
            )

        # Guardar todos los permisos de una sola vez
        PermisoZona.objects.bulk_create(permisos_a_crear)

        messages.success(request, "Usuario del sistema creado correctamente con sus permisos de zona.")
        return redirect("adminUsuario")

    return movimiento_boton_navegador(request, "carpAdmin/crearUsuario.html")


import json


@csrf_exempt
def editar_usuario_ajax(request, usuario_id):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            usuario = UsuarioSistema.objects.get(id=usuario_id)
            for campo, valor in data.items():
                # Convertir booleano si el campo es activo
                if campo == "activo":
                    valor = True if valor in [True, "true", "True", "1"] else False
                setattr(usuario, campo, valor)
            usuario.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False})



@csrf_exempt
def eliminar_usuario(request, usuario_id):
    if request.method == "POST":
        try:
            usuario = UsuarioSistema.objects.get(id=usuario_id)
            usuario.delete()
            return JsonResponse({"success": True})
        except UsuarioSistema.DoesNotExist:
            return JsonResponse({"success": False, "error": "Usuario no encontrado"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido"})



#zona 

def adminZonas(request):
    """Lista de zonas con buscador y paginación."""
    query = request.GET.get("q", "").strip()
    zonas_list = Zona.objects.all().order_by("id")

    if query:
        zonas_list = zonas_list.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )

    paginator = Paginator(zonas_list, 8)
    page_number = request.GET.get("page")
    zonas = paginator.get_page(page_number)

    context = {
        "zonas": zonas,
        "query": query,
        "mostrar_menu": request.session.get("mostrar_menu", True),
    }
    return movimiento_boton_navegador(request, "carpAdmin/adminZonas.html", context)



def crear_zona(request):
    """Crea una nueva zona y genera permisos automáticos para todos los usuarios."""
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        tipo_zona = request.POST.get("tipo_zona")

        # Verificar nombre duplicado
        if Zona.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, "Ya existe una zona con ese nombre.")
            return redirect("crear_zona")

        # Crear la zona
        nueva_zona = Zona(nombre=nombre, descripcion=descripcion, tipo_zona=tipo_zona)
        nueva_zona.save()

        # 🔹 Crear permisos automáticos para todos los usuarios del sistema
        usuarios = UsuarioSistema.objects.all()
        permisos_a_crear = []

        for usuario in usuarios:
            # Si la zona es pública → acceso habilitado
            acceso = True if tipo_zona == "publica" else False
            permisos_a_crear.append(
                PermisoZona(usuario=usuario, zona=nueva_zona, acceso_habilitado=acceso)
            )

        # Guardar todos los permisos en bloque
        if permisos_a_crear:
            PermisoZona.objects.bulk_create(permisos_a_crear)

        messages.success(request, "Zona creada correctamente con permisos asignados a todos los usuarios.")
        return redirect("adminZonas")

    return movimiento_boton_navegador(request, "carpAdmin/crearZona.html")



def ver_zona(request, zona_id):
    zona = get_object_or_404(Zona, id=zona_id)
    query = request.GET.get("q", "").strip()

    permisos = PermisoZona.objects.filter(zona=zona).select_related('usuario')

    if query:
        permisos = permisos.filter(
            Q(usuario__nombres__icontains=query) |
            Q(usuario__apellidos__icontains=query) |
            Q(usuario__rut__icontains=query)
        )

    return movimiento_boton_navegador(request, "carpAdmin/verZona.html", {
        "zona": zona,
        "permisos": permisos,
        "query": query,
        "mostrar_menu": request.session.get("mostrar_menu", True),
    })


@csrf_exempt
def cambiar_permiso_zona(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        permiso_id = data.get("permiso_id")
        acceso_habilitado = data.get("acceso_habilitado")

        try:
            permiso = PermisoZona.objects.get(id=permiso_id)
            permiso.acceso_habilitado = acceso_habilitado
            permiso.save()
            return JsonResponse({"success": True})
        except PermisoZona.DoesNotExist:
            return JsonResponse({"success": False, "error": "Permiso no encontrado."})
    return JsonResponse({"success": False, "error": "Método no permitido."})



def eliminar_zona(request, zona_id):
    """Elimina una zona con confirmación."""
    zona = get_object_or_404(Zona, id=zona_id)
    zona.delete()
    messages.success(request, f"La zona '{zona.nombre}' fue eliminada correctamente.")
    return redirect("adminZonas")