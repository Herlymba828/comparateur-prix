// Gestion de l'authentification
document.addEventListener('DOMContentLoaded', function () {
    initAuthForms();
});

// Initialiser les formulaires d'authentification
function initAuthForms() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

// Gérer la connexion
function handleLogin(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const email = formData.get('email');
    const password = formData.get('password');

    // Validation basique
    if (!validateEmail(email)) {
        showError('email', 'Email invalide');
        return;
    }

    if (password.length < 6) {
        showError('password', 'Le mot de passe doit contenir au moins 6 caractères');
        return;
    }

    // Simuler une requête API
    simulateAuthRequest('login', { email, password })
        .then(response => {
            if (response.success) {
                // Rediriger vers la page d'accueil après connexion réussie
                window.location.href = 'index.html';
            } else {
                showError('password', 'Email ou mot de passe incorrect');
            }
        })
        .catch(error => {
            showError('password', 'Erreur de connexion');
        });
}

// Gérer l'inscription
function handleRegister(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const name = formData.get('name');
    const email = formData.get('email');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm-password');

    // Validation
    if (name.length < 2) {
        showError('name', 'Le nom doit contenir au moins 2 caractères');
        return;
    }

    if (!validateEmail(email)) {
        showError('email', 'Email invalide');
        return;
    }

    if (password.length < 6) {
        showError('password', 'Le mot de passe doit contenir au moins 6 caractères');
        return;
    }

    if (password !== confirmPassword) {
        showError('confirm-password', 'Les mots de passe ne correspondent pas');
        return;
    }

    // Simuler une requête API
    simulateAuthRequest('register', { name, email, password })
        .then(response => {
            if (response.success) {
                // Rediriger vers la page de connexion après inscription réussie
                alert('Inscription réussie ! Vous pouvez maintenant vous connecter.');
                window.location.href = 'connexion.html';
            } else {
                showError('email', 'Cet email est déjà utilisé');
            }
        })
        .catch(error => {
            showError('email', 'Erreur lors de l\'inscription');
        });
}

// Valider l'email
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Afficher une erreur
function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}-error`) || createErrorElement(fieldId);

    field.classList.add('error');
    errorElement.textContent = message;
    errorElement.classList.add('show');
}

// Créer un élément d'erreur
function createErrorElement(fieldId) {
    const errorElement = document.createElement('div');
    errorElement.id = `${fieldId}-error`;
    errorElement.className = 'error-message';

    const field = document.getElementById(fieldId);
    field.parentNode.appendChild(errorElement);

    return errorElement;
}

// Simuler une requête d'authentification
function simulateAuthRequest(endpoint, data) {
    return new Promise((resolve) => {
        setTimeout(() => {
            // Simulation basique - en réalité, cela appellerait une API
            if (endpoint === 'login') {
                resolve({ success: data.email === 'test@example.com' && data.password === 'password' });
            } else if (endpoint === 'register') {
                // Toujours réussir pour la démo
                resolve({ success: true });
            }
        }, 1000);
    });
}

// Vérifier si l'utilisateur est connecté (simulation)
function isLoggedIn() {
    return localStorage.getItem('userToken') !== null;
}

// Déconnexion
function logout() {
    localStorage.removeItem('userToken');
    window.location.href = 'index.html';
}