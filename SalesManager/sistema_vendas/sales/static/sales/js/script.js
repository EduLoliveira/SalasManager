
// Toggle dropdown do usuário
const avatarButton = document.getElementById('avatarButton');
const dropdownMenu = document.getElementById('dropdownMenu');

avatarButton.addEventListener('click', function (e) {
    e.stopPropagation();
    dropdownMenu.classList.toggle('show');
    avatarButton.classList.toggle('active');
});

// Fechar o dropdown ao clicar fora dele
window.addEventListener('click', function () {
    if (dropdownMenu.classList.contains('show')) {
        dropdownMenu.classList.remove('show');
        avatarButton.classList.remove('active');
    }
});

// Prevenir que cliques dentro do dropdown fechem ele
dropdownMenu.addEventListener('click', function (e) {
    e.stopPropagation();
});

// Toggle para mostrar mais clientes
const viewAllButton = document.getElementById('viewAllButton');
const moreClients = document.getElementById('moreClients');
let clientsExpanded = false;

viewAllButton.addEventListener('click', function () {
    clientsExpanded = !clientsExpanded;
    moreClients.classList.toggle('show', clientsExpanded);

    if (clientsExpanded) {
        viewAllButton.innerHTML = 'Ver menos <i class="fas fa-chevron-up"></i>';
    } else {
        viewAllButton.innerHTML = 'Ver todos <i class="fas fa-chevron-down"></i>';
    }
});
