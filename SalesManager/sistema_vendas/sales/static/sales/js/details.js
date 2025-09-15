
// Função para mostrar a notificação
function showNotification(vendaData) {
    const notification = document.getElementById('successNotification');
    document.getElementById('notif-cliente').textContent = vendaData.cliente || 'Não informado';
    document.getElementById('notif-quantidade').textContent = vendaData.quantidade || 'Não informado';
    document.getElementById('notif-valor').textContent = vendaData.valor ? 'R$ ' + parseFloat(vendaData.valor).toFixed(2) : 'Não informado';
    document.getElementById('notif-data').textContent = vendaData.data_venda || 'Não informado';
    notification.style.display = 'block';
    window.notificationTimeout = setTimeout(hideNotification, 10000);
}

// Função para esconder a notificação
function hideNotification() {
    const notification = document.getElementById('successNotification');
    if (notification) {
        notification.style.display = 'none';
    }
    if (window.notificationTimeout) {
        clearTimeout(window.notificationTimeout);
    }
    fetch('/clear_venda_session/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    }).catch(error => console.error('Error:', error));
}

// Função para obter o cookie CSRF
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

// Aguarda o documento carregar completamente
document.addEventListener('DOMContentLoaded', function () {

    // Código para o botão de filtros
    const toggleButton = document.getElementById('toggleFiltersBtn');
    const filtersContent = document.getElementById('filtersContent');

    if (toggleButton && filtersContent) {
        toggleButton.addEventListener('click', function () {
            filtersContent.classList.toggle('hidden');
            const isHidden = filtersContent.classList.contains('hidden');
            if (isHidden) {
                toggleButton.innerHTML = '<i class="bi bi-sliders"></i> Visualizar Filtros';
            } else {
                toggleButton.innerHTML = '<i class="bi bi-x-lg"></i> Ocultar Filtros';
            }
        });
    }

    // Verificar se há dados de venda na sessão para exibir notificação
    fetch('/check_venda_session/')
        .then(response => response.json())
        .then(data => {
            if (data.has_venda_data) {
                showNotification(data.venda_data);
            }
        })
        .catch(error => console.error('Error:', error));

    // Evento de submit ao pressionar Enter na busca
    const searchInput = document.querySelector('input[name="busca"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.form.submit();
            }
        });
    }

    // Submissão automática ao alterar a ordenação
    const orderBySelect = document.getElementById('ordenar_por');
    if (orderBySelect) {
        orderBySelect.addEventListener('change', function () {
            this.form.submit();
        });
    }

    // Submissão automática ao alterar o status
    const statusSelect = document.getElementById('status');
    if (statusSelect) {
        statusSelect.addEventListener('change', function () {
            this.form.submit();
        });
    }

});
