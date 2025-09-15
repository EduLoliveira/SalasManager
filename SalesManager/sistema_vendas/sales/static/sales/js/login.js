
// ✅ APENAS FUNÇÕES ESSENCIAIS

// 1. Função para mostrar/ocultar senha
function togglePassword(inputId) {
    const passwordInput = document.getElementById(inputId);
    const toggleIcon = passwordInput.parentElement.querySelector('.password-toggle i');

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

// 2. Auto-dismiss para mensagens do Django
document.addEventListener('DOMContentLoaded', function () {
    // Fechar mensagens automaticamente após alguns segundos
    const alerts = document.querySelectorAll('.alert-django');

    alerts.forEach(alert => {
        // Mensagens de sucesso: 5 segundos
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }

        // Mensagens de erro: 8 segundos
        if (alert.classList.contains('alert-danger')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 8000);
        }
    });

    // 3. Validação básica front-end (opcional)
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            const username = document.getElementById('id_username').value.trim();
            const password = document.getElementById('id_password').value;

            let hasError = false;

            // Validar username
            if (!username) {
                document.getElementById('id_username').classList.add('is-invalid');
                hasError = true;
            }

            // Validar senha
            if (!password) {
                document.getElementById('id_password').classList.add('is-invalid');
                hasError = true;
            }

            if (hasError) {
                e.preventDefault();
                return;
            }

            // Mostrar loading no botão
            const loginButton = document.getElementById('login-button');
            if (loginButton) {
                loginButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Entrando...';
                loginButton.disabled = true;
            }
        });
    }

    // 4. Remover validação quando usuário começar a digitar
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');

    if (usernameInput) {
        usernameInput.addEventListener('input', function () {
            this.classList.remove('is-invalid');
        });
    }

    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            this.classList.remove('is-invalid');
        });
    }
});
