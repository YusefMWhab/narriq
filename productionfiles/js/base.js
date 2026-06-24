function showAlert(message, type = 'info') {
    const messagesContainer = document.getElementById('django-messages');
    if (!messagesContainer) return;

    messagesContainer.innerHTML = '';

    const errorBody = messagesContainer.closest('.error-body');
    if (errorBody) errorBody.style.display = 'block';

    const alertBox = document.createElement('div');
    
    let alertClass = type;
    if (type === 'danger') alertClass = 'error';
    
    alertBox.className = `alert alert-${alertClass}`;
    alertBox.innerText = message;

    messagesContainer.appendChild(alertBox);

    setTimeout(() => {
        alertBox.classList.add('animate-fade-in');
    }, 10);

    setTimeout(() => {
        alertBox.classList.remove('animate-fade-in');
        alertBox.classList.add('animate-fade-out');
        
        setTimeout(() => {
            alertBox.remove();
        }, 400);
        
    }, 4000);
}

async function confirmWindow(message) {
    const result = await Swal.fire({
        title: 'Are you sure?',
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#a855f7', 
        cancelButtonColor: '#64748b',   
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
        background: '#17123a', 
        color: '#ffffff',
        iconColor: '#a855f7'
    });

    return result.isConfirmed; 
}

async function promptWindow(title, placeholderText) {
    const { value: textInput } = await Swal.fire({
        title: title,
        input: 'text',
        inputPlaceholder: placeholderText,
        showCancelButton: true,
        confirmButtonColor: '#a855f7', 
        cancelButtonColor: '#64748b',   
        confirmButtonText: 'Submit',
        cancelButtonText: 'Cancel',
        background: '#17123a', 
        color: '#ffffff',
        iconColor: '#a855f7',
        customClass: {
            input: 'swal-custom-input'
        },
    });

    return textInput ? textInput.trim() : null;
}

async function Select_DropdownWindow(title, options) {
    const html = `
        <select id="merge-select">
            <option value="">Select destination code...</option>
            ${Object.entries(options)
                .map(([id, text]) => `<option value="${id}">${text}</option>`)
                .join('')}
        </select>
    `;

    const result = await Swal.fire({
        title,
        html,
        width: 650,
        grow: false,
        showCancelButton: true,
        confirmButtonColor: '#a855f7', 
        cancelButtonColor: '#64748b',   
        confirmButtonText: 'Submit',
        cancelButtonText: 'Cancel',
        background: '#17123a', 
        color: '#ffffff',
        iconColor: '#a855f7',
        didOpen: () => {
            new TomSelect('#merge-select', {
                create: false,
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });
        },
        preConfirm: () => {
            const value = document.getElementById('merge-select').value;

            if (!value) {
                Swal.showValidationMessage(
                    'You must select a code to merge into!'
                );
                return false;
            }

            return value;
        }
    });

    return result.value || null;
}


document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach((alert) => {
        // show animation
        setTimeout(() => {
            alert.classList.add("show");
        }, 50);

        // hide after 4 seconds
        setTimeout(() => {
            alert.classList.remove("show");

            // optional: remove from DOM after fade out
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 4000);
    });
});
