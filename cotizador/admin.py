from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Servicio

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'codigo_tramite', 'valor_uf', 'descripcion')
    list_filter = ('categoria',)
    search_fields = ('codigo_tramite', 'descripcion')