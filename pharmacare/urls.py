"""pharmacare URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from cotizador import views

# 1. Asegúrate de importar la función 'home' además del webhook
from cotizador.views import whatsapp_webhook, home 

urlpatterns = [
    # 2. Esta es la línea clave que evita el error "Not Found: /"
    path('', home, name='home'), 
    
    path('admin/', admin.site.urls),
    path('api/whatsapp/webhook/', whatsapp_webhook),
    path('api/whatsapp/aprobar/<int:ticket_id>/', views.aprobar_cotizacion, name='aprobar_cotizacion'),
    path('api/whatsapp/rechazar/<int:ticket_id>/', views.rechazar_cotizacion, name='rechazar_cotizacion'),
]

# 3. Esto conecta los archivos CSS y JS
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])