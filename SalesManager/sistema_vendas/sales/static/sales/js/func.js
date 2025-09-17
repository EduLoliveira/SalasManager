// Script para controlar a exibição da lista (versão simplificada)
document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('toggleListBtn');
    const vendasContainer = document.getElementById('vendasContainer');

    if (toggleBtn && vendasContainer) {
        toggleBtn.addEventListener('click', function () {
            vendasContainer.classList.toggle('expanded');

            if (vendasContainer.classList.contains('expanded')) {
                toggleBtn.innerHTML = '<i class="bi bi-chevron-up"></i> Ocultar lista';
            } else {
                toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> Exibir todos os clientes';
            }
        });
    }

    // Remover o cursor de pointer dos nomes de clientes
    const clienteNomes = document.querySelectorAll('.cliente-nome');
    clienteNomes.forEach(nome => {
        nome.style.cursor = 'default'; // Ou remova completamente: nome.style.cursor = '';
    });
});