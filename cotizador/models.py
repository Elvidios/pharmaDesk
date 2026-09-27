from django.db import models


class Servicio(models.Model):
    CATEGORIAS = [
        ('CO', 'Cosméticos'),
        ('DM', 'Dispositivos Médicos'),
        ('AL', 'Alimentos'),
    ]
    
    categoria = models.CharField(max_length=2, choices=CATEGORIAS)
    codigo_tramite = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.TextField()
    valor_uf = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.descripcion[:50]}"

class Ticket(models.Model):
    numero_cliente = models.CharField(max_length=50)
    categoria = models.CharField(max_length=50)
    tramite = models.CharField(max_length=100)
    borrador_cotizacion = models.TextField()
    estado = models.CharField(max_length=20, default='Pendiente') # 'Pendiente' o 'Aprobado'
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.categoria} - {self.numero_cliente} ({self.estado})"