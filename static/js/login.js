// ============================================
// JavaScript do Login - Portal Maestro
// ============================================

let currentUsername = '';
let currentStep = 1;

// Toggle de visibilidade da senha
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const passwordToggle = document.getElementById('passwordToggle');
    const icon = passwordToggle.querySelector('i');
    
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    icon.classList.toggle('fa-eye');
    icon.classList.toggle('fa-eye-slash');
}

// Voltar para o step 1
function goBackToStep1() {
    currentStep = 1;
    updateStepIndicator();
    showStep(1);
}

// Atualizar indicador de progresso
function updateStepIndicator() {
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    if (step1) step1.classList.toggle('active', currentStep >= 1);
    if (step2) step2.classList.toggle('active', currentStep >= 2);
}

// Mostrar step específico
function showStep(step) {
    const step1 = document.getElementById('loginFormStep1');
    const step2 = document.getElementById('loginFormStep2');
    const backButton = document.getElementById('backButton');
    
    if (step === 1) {
        if (step1) step1.classList.add('active');
        if (step2) step2.classList.remove('active');
        if (backButton) backButton.classList.remove('show');
        const usernameInput = document.getElementById('username');
        if (usernameInput) usernameInput.focus();
    } else {
        if (step1) step1.classList.remove('active');
        if (step2) step2.classList.add('active');
        if (backButton) backButton.classList.add('show');
        const passwordInput = document.getElementById('password');
        if (passwordInput) passwordInput.focus();
    }
}

// Mostrar erro
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.classList.add('show');
        setTimeout(() => {
            errorMessage.classList.remove('show');
        }, 5000);
    }
}

// Set loading state
function setLoading(step, loading) {
    const spinner = document.getElementById(`loadingSpinner${step}`);
    const button = step === 1 ? document.getElementById('btnContinue') : document.getElementById('btnLogin');
    const text = step === 1 ? document.getElementById('continueText') : document.getElementById('loginText');
    
    if (loading) {
        if (button) button.disabled = true;
        if (text) text.style.display = 'none';
        if (spinner) spinner.classList.add('show');
    } else {
        if (button) button.disabled = false;
        if (text) text.style.display = 'block';
        if (spinner) spinner.classList.remove('show');
    }
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Step 1: Validar username e avançar
    const formStep1 = document.getElementById('loginFormStep1');
    if (formStep1) {
        formStep1.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value.trim();
            
            if (!username) {
                showError('Por favor, digite seu usuário');
                return;
            }

            setLoading(1, true);
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage) errorMessage.classList.remove('show');

            // Avançar para o próximo step
            setTimeout(() => {
                currentUsername = username;
                currentStep = 2;
                updateStepIndicator();
                showStep(2);
                setLoading(1, false);
                
                // Preencher o campo hidden com o username
                const hiddenUsername = document.getElementById('hiddenUsername');
                if (hiddenUsername) {
                    hiddenUsername.value = username;
                }
            }, 300);
        });
    }

    // Step 2: Fazer login (form POST tradicional do Flask)
    const formStep2 = document.getElementById('loginFormStep2');
    if (formStep2) {
        formStep2.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;

            if (!password) {
                e.preventDefault();
                showError('Por favor, digite sua senha');
                return;
            }

            // Limpar mensagens de erro
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage) errorMessage.classList.remove('show');

            // Mostrar loading visualmente (mas não desabilitar o botão para não impedir o submit)
            const spinner = document.getElementById('loadingSpinner2');
            const loginText = document.getElementById('loginText');
            if (spinner) spinner.classList.add('show');
            if (loginText) loginText.textContent = 'Entrando...';

            // NÃO chamar preventDefault() e NÃO desabilitar o botão
            // Deixar o formulário ser submetido normalmente
            // O Flask processará e redirecionará automaticamente
        });
    }

    // Enter para avançar no step 1
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (formStep1) {
                    formStep1.dispatchEvent(new Event('submit'));
                }
            }
        });
    }

    // Enter para fazer login no step 2
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                // Permitir submit normal do form
            }
        });
    }

    // Verificar se há mensagens de erro do Flask (flash messages)
    const flaskErrorMessage = document.getElementById('flaskErrorMessage');
    if (flaskErrorMessage) {
        // Se houver erro do Flask, mostrar no step 2 (assumindo que o usuário já tentou fazer login)
        currentStep = 2;
        updateStepIndicator();
        showStep(2);
        
        // Copiar mensagem para o errorMessage também
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.textContent = flaskErrorMessage.textContent.trim();
            errorMessage.classList.add('show');
        }
    }
});

