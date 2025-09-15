
// Função para alternar entre as etapas do formulário
function goToStep(stepNumber) {
    // Esconder todas as etapas
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });

    // Mostrar a etapa atual
    document.getElementById(`step-${stepNumber}`).classList.add('active');

    // Atualizar o indicador de etapas
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
        if (parseInt(step.getAttribute('data-step')) === stepNumber) {
            step.classList.add('active');
        }
    });
}

// Adicionar event listeners para os botões de navegação
document.getElementById('next-to-step-2').addEventListener('click', function () {
    // Validar os campos da primeira etapa antes de prosseguir
    let isValid = true;

    // Validar nome
    const firstName = document.getElementById('first_name').value;
    if (!firstName) {
        document.getElementById('first_name_error').textContent = 'Por favor, informe seu nome.';
        isValid = false;
        document.getElementById('first_name').focus();
    } else {
        document.getElementById('first_name_error').textContent = '';
    }

    // Validar sobrenome
    const lastName = document.getElementById('last_name').value;
    if (!lastName) {
        document.getElementById('last_name_error').textContent = 'Por favor, informe seu sobrenome.';
        isValid = false;
        if (isValid) document.getElementById('last_name').focus();
    } else {
        document.getElementById('last_name_error').textContent = '';
    }

    // Validar email
    const email = document.getElementById('email').value;
    if (!email) {
        document.getElementById('email_error').textContent = 'Por favor, informe seu email.';
        isValid = false;
        if (isValid) document.getElementById('email').focus();
    } else if (!isValidEmail(email)) {
        document.getElementById('email_error').textContent = 'Por favor, informe um email válido.';
        isValid = false;
        if (isValid) document.getElementById('email').focus();
    } else {
        document.getElementById('email_error').textContent = '';
    }

    // Validar telefone
    const telefone = document.getElementById('telefone').value;
    if (!telefone) {
        document.getElementById('telefone_error').textContent = 'Por favor, informe seu telefone.';
        isValid = false;
        if (isValid) document.getElementById('telefone').focus();
    } else {
        document.getElementById('telefone_error').textContent = '';
    }

    if (isValid) {
        goToStep(2);
    }
});

document.getElementById('prev-to-step-1').addEventListener('click', function () {
    goToStep(1);
});

// Função para validar email
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Função para mostrar/ocultar senha
function togglePassword(inputId) {
    const passwordInput = document.getElementById(inputId);
    const toggleIcon = passwordInput.parentElement.nextElementSibling.querySelector('i');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('bi-eye');
        toggleIcon.classList.add('bi-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('bi-eye-slash');
        toggleIcon.classList.add('bi-eye');
    }
}

// Validação do formulário completo no envio
document.getElementById('registration-form').addEventListener('submit', function (e) {
    e.preventDefault();

    let isValid = true;
    let firstErrorField = null;

    // Validar username
    const username = document.getElementById('username').value;
    if (!username) {
        document.getElementById('username_error').textContent = 'Por favor, informe um username.';
        isValid = false;
        if (!firstErrorField) firstErrorField = document.getElementById('username');
    } else {
        document.getElementById('username_error').textContent = '';
    }

    // Validar senha
    const password1 = document.getElementById('password1').value;
    if (!password1) {
        document.getElementById('password1_error').textContent = 'Por favor, informe uma senha.';
        isValid = false;
        if (!firstErrorField) firstErrorField = document.getElementById('password1');
    } else if (password1.length < 8) {
        document.getElementById('password1_error').textContent = 'A senha deve ter pelo menos 8 caracteres.';
        isValid = false;
        if (!firstErrorField) firstErrorField = document.getElementById('password1');
    } else {
        document.getElementById('password1_error').textContent = '';
    }

    // Validar confirmação de senha
    const password2 = document.getElementById('password2').value;
    if (!password2) {
        document.getElementById('password2_error').textContent = 'Por favor, confirme sua senha.';
        isValid = false;
        if (!firstErrorField) firstErrorField = document.getElementById('password2');
    } else if (password1 !== password2) {
        document.getElementById('password2_error').textContent = 'As senhas não coincidem.';
        isValid = false;
        if (!firstErrorField) firstErrorField = document.getElementById('password2');
    } else {
        document.getElementById('password2_error').textContent = '';
    }

    if (!isValid && firstErrorField) {
        firstErrorField.focus();
        return;
    }

    if (isValid) {
        // Simular envio bem-sucedido do formulário
        alert('Conta criada com sucesso! Redirecionando para o login...');
        // Aqui você enviaria o formulário para o servidor
        this.submit();
    }
});
