let currentTicketId = null;

// ==========================================
// 1. LÓGICA DE VISTA PREVIA Y APROBACIÓN INDIVIDUAL
// ==========================================

function openPreview(realId, displayId, cliente, tramite, borrador) {
    currentTicketId = realId; // Guardamos el ID real para la aprobación
    document.getElementById('modalId').innerText = displayId;
    document.getElementById('modalClient').innerText = cliente;
    document.getElementById('modalService').innerText = tramite;
    document.getElementById('modalValue').innerText = borrador;
    
    document.getElementById('previewModal').style.display = 'flex'; 
}

function closePreview() {
    document.getElementById('previewModal').style.display = 'none';
}

function aprobarCotizacion() {
    if (!currentTicketId) return;

    // Cambiar el texto del botón a "Enviando..."
    const btn = document.getElementById('btn-approve-single');
    const originalText = btn.innerText;
    btn.innerText = "Enviando...";
    btn.disabled = true;

    // Hacer una petición AJAX a Django
    fetch(`/api/whatsapp/aprobar/${currentTicketId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), // Usamos tu función getCookie
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('¡Cotización aprobada y enviada al cliente!');
            closePreview();
            location.reload(); // Recargar la página para actualizar la tabla
        } else {
            alert('Error: ' + data.message);
            btn.innerText = originalText;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Hubo un error al procesar la aprobación.');
        btn.innerText = originalText;
        btn.disabled = false;
    });
}

// ==========================================
// 2. LÓGICA DE CHECKBOXES Y APROBACIÓN MÚLTIPLE
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.row-checkbox'); // Capturamos todos los de las filas
    
    if (selectAllCheckbox && checkboxes.length > 0) {
        
        // Regla 1: De arriba hacia abajo (El jefe manda)
        selectAllCheckbox.addEventListener('change', function() {
            checkboxes.forEach(cb => {
                cb.checked = this.checked;
            });
        });

        // Regla 2: De abajo hacia arriba (Los empleados informan al jefe)
        checkboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                // Verificamos si la cantidad de marcados es igual a la cantidad total
                const todosEstanMarcados = Array.from(checkboxes).every(c => c.checked);
                
                // Actualizamos el estado del checkbox principal
                selectAllCheckbox.checked = todosEstanMarcados;
            });
        });
    }
});

function aprobarSeleccionados() {
    // Recolectamos los IDs de las filas marcadas
    const seleccionados = Array.from(document.querySelectorAll('.row-checkbox:checked'))
                              .map(cb => cb.value);

    if (seleccionados.length === 0) {
        alert("⚠️ Por favor, selecciona al menos un ticket de la lista.");
        return;
    }

    if (confirm(`¿Enviar cotización a los ${seleccionados.length} clientes seleccionados?`)) {
        
        // Creamos una ráfaga de peticiones (una por cada ticket)
        let promesas = seleccionados.map(id => {
            return fetch(`/api/whatsapp/aprobar/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });
        });

        // Esperamos a que todas terminen
        Promise.all(promesas)
            .then(() => {
                alert(`✅ ${seleccionados.length} cotizaciones enviadas con éxito.`);
                location.reload(); 
            })
            .catch(error => {
                console.error("Error en el envío masivo:", error);
                alert("Hubo un error al procesar algunos envíos.");
            });
    }
}

// ==========================================
// 3. FUNCIONES AUXILIARES
// ==========================================

// Función auxiliar para obtener el token CSRF de Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ==========================================
// 4. LÓGICA DE RECHAZO
// ==========================================

function rechazarSeleccionados() {
    // Recolectamos los IDs de las filas marcadas
    const seleccionados = Array.from(document.querySelectorAll('.row-checkbox:checked'))
                              .map(cb => cb.value);

    if (seleccionados.length === 0) {
        alert("⚠️ Por favor, selecciona al menos un ticket para rechazar.");
        return;
    }

    if (confirm(`¿Estás seguro de que deseas eliminar los ${seleccionados.length} tickets seleccionados?`)) {
        let promesas = seleccionados.map(id => {
            return fetch(`/api/whatsapp/rechazar/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            }).then(response => {
                if (!response.ok) throw new Error('Error en el servidor de Django');
                return response.json();
            });
        });

        Promise.all(promesas)
            .then(() => {
                alert(`✅ ${seleccionados.length} solicitudes rechazadas y eliminadas.`);
                location.reload(); 
            })
            .catch(error => {
                console.error("Error en el rechazo masivo:", error);
                alert("Hubo un error al eliminar algunos tickets.");
            });
    }
}