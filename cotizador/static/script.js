let currentTicketId = null;

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
            'X-CSRFToken': getCookie('csrftoken'), // Necesario para peticiones POST en Django
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