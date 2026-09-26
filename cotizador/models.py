from django.db import models

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