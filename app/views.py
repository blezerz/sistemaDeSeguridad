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
    return movimiento_boton_navegador(request, 'index.html')

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
                return redirect("../inicioAdmin/")
            elif user.groups.filter(name="Operador").exists():
                return redirect("../inicioOperador/")
            elif user.groups.filter(name="UsuarioBasico").exists():
                return redirect("../inicioUsuarioBasico")
            else:
                return redirect("/")  # fallback
        else:
            return render(request, "login.html", {"error": "Usuario o contraseña incorrectos"})

    return render(request, "login.html")





def logout_view(request):
    return redirect("../login")


def prueba(request):
    # Estado inicial: siempre True la primera vez
    if "mostrar_menu" not in request.session:
        request.session["mostrar_menu"] = True

    mostrar_menu = request.session["mostrar_menu"]

    # ⚡ Solo cambiar si llega el toggle
    if "toggle" in request.GET:
        mostrar_menu = not mostrar_menu
        request.session["mostrar_menu"] = mostrar_menu
        # Redirigir para limpiar la URL y evitar doble toggle al F5
        return redirect("prueba")  # 👈 usa el name de tu URL en urls.py

    return render(request, "prueba.html", {"mostrar_menu": mostrar_menu})






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
    return movimiento_boton_navegador(request, "inicioAdmin.html")



def inicioOperador(request):
    zonas_list = Zona.objects.all().order_by('id')  # Ordenar por ID o nombre si prefieres
    paginator = Paginator(zonas_list, 5)  # 👈 5 zonas por página

    page_number = request.GET.get('page')
    zonas = paginator.get_page(page_number)

    return movimiento_boton_navegador(request, "inicioOperador.html", {
        "zonas": zonas,
        "paginator": paginator,
    })

def operadorRegistroAcceso(request, zona_id):
    zona = Zona.objects.get(id=zona_id)
    return render(request, "operadorRegistroAcceso.html", {"zona": zona})


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
    return movimiento_boton_navegador(request, "adminUsuario.html")