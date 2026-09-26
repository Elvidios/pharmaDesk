// Lógica para Selección Múltiple y Botones de Acción
const selectAllCheckbox = document.getElementById('selectAll');
const rowCheckboxes = document.querySelectorAll('.row-checkbox');
const btnApprove = document.getElementById('btn-approve');
const btnReject = document.getElementById('btn-reject');

// Función para habilitar/deshabilitar botones si hay algo seleccionado
function updateActionButtons() {
    const anyChecked = Array.from(rowCheckboxes).some(cb => cb.checked);
    btnApprove.disabled = !anyChecked;
    btnReject.disabled = !anyChecked;
}

// Checkbox Maestro (Seleccionar todo)
selectAllCheckbox.addEventListener('change', function() {
    rowCheckboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
    });
    updateActionButtons();
});

// Checkboxes individuales
rowCheckboxes.forEach(cb => {
    cb.addEventListener('change', function() {
        // Si desmarcas uno, el maestro se desmarca
        if (!this.checked) {
            selectAllCheckbox.checked = false;
        }
        // Si marcas todos manualmente, el maestro se marca
        if (Array.from(rowCheckboxes).every(c => c.checked)) {
            selectAllCheckbox.checked = true;
        }
        updateActionButtons();
    });
});

// Lógica del Panel de Vista Previa (Slide-out)
const modal = document.getElementById('previewModal');

function openPreview(id, client, service, value) {
    // Llenar datos dinámicos en el panel
    document.getElementById('modalId').textContent = id;
    document.getElementById('modalClient').textContent = client;
    document.getElementById('modalService').textContent = service;
    document.getElementById('modalValue').textContent = value;
    
    // Mostrar el modal
    modal.style.display = 'flex';
}

function closePreview() {
    modal.style.display = 'none';
}

// Cerrar al hacer clic fuera del panel derecho
modal.addEventListener('click', function(e) {
    if (e.target === modal) {
        closePreview();
    }
});