// Chargement des composants communs
document.addEventListener('DOMContentLoaded', function () {
    loadHeader();
    loadFooter();
    initializeApp();
    setActiveNavLink();

    // Charger les données spécifiques à la page
    loadPageSpecificContent();
});

// Charger le header
function loadHeader() {
    fetch('/components/header.html')
        .then(response => {
            if (!response.ok) {
                throw new Error('Header non trouvé');
            }
            return response.text();
        })
        .then(data => {
            document.getElementById('header').innerHTML = data;
            setActiveNavLink();
        })
        .catch(error => {
            console.error('Erreur lors du chargement du header:', error);
            document.getElementById('header').innerHTML = `
                <div class="header-container">
                    <a href="/" class="logo">ComparateurPrix</a>
                    <nav>
                        <ul class="nav-menu">
                            <li><a href="/">Accueil</a></li>
                            <li><a href="/produits/">Produits</a></li>
                            <li><a href="/magasins/">Magasins</a></li>
                            <li><a href="/recommandations/">Recommandations</a></li>
                            <li><a href="/analyses/">Analyses</a></li>
                        </ul>
                    </nav>
                    <div class="auth-buttons">
                        <a href="/connexion/" class="btn">Connexion</a>
                        <a href="/inscription/" class="btn btn-secondary">Inscription</a>
                    </div>
                </div>
            `;
            setActiveNavLink();
        });
}

// Charger le footer
function loadFooter() {
    fetch('/components/footer.html')
        .then(response => {
            if (!response.ok) {
                throw new Error('Footer non trouvé');
            }
            return response.text();
        })
        .then(data => {
            document.getElementById('footer').innerHTML = data;
        })
        .catch(error => {
            console.error('Erreur lors du chargement du footer:', error);
            document.getElementById('footer').innerHTML = `
                <div class="footer-content">
                    <div class="footer-section">
                        <h3>Comparateur de Prix</h3>
                        <p>Trouvez les meilleurs prix près de chez vous</p>
                    </div>
                    <div class="footer-section">
                        <h3>Liens rapides</h3>
                        <ul>
                            <li><a href="/">Accueil</a></li>
                            <li><a href="/produits/">Produits</a></li>
                            <li><a href="/magasins/">Magasins</a></li>
                        </ul>
                    </div>
                    <div class="footer-section">
                        <h3>Contact</h3>
                        <p>Email: contact@comparateur.fr</p>
                        <p>Téléphone: +33 1 23 45 67 89</p>
                    </div>
                </div>
                <div class="footer-bottom">
                    <p>&copy; 2024 Comparateur de Prix. Tous droits réservés.</p>
                </div>
            `;
        });
}

// Initialiser l'application
function initializeApp() {
    console.log('Application Comparateur de Prix initialisée');

    // Initialiser les écouteurs d'événements globaux
    initGlobalEventListeners();
}

// Initialiser les écouteurs d'événements globaux
function initGlobalEventListeners() {
    // Gestion de la recherche globale
    const searchInput = document.querySelector('.search-bar input');
    const searchButton = document.querySelector('.search-bar button');

    if (searchInput && searchButton) {
        searchButton.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

// Marquer le lien actif dans la navigation
function setActiveNavLink() {
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a');

    navLinks.forEach(link => {
        try {
            const href = new URL(link.href, window.location.origin).pathname;
            if (href === '/' && path === '/') link.classList.add('active');
            else if (href !== '/' && path.startsWith(href)) link.classList.add('active');
        } catch (_) {}
    });
}

// Charger le contenu spécifique à la page
function loadPageSpecificContent() {
    const path = window.location.pathname;
    if (path === '/' || path === '') {
        loadPopularProducts();
    } else if (path.startsWith('/produits/')) {
        initProductFilters();
        loadProducts();
    } else if (path.startsWith('/magasins/')) {
        loadStores();
    } else if (path.startsWith('/recommandations/')) {
        loadRecommendations();
    } else if (path.startsWith('/analyses/')) {
        loadAnalytics();
    }
}

// Effectuer une recherche
function performSearch() {
    const searchInput = document.querySelector('.search-bar input');
    const searchTerm = searchInput ? searchInput.value.trim() : '';

    if (searchTerm) {
        window.location.href = `/produits/?search=${encodeURIComponent(searchTerm)}`;
    }
}

// Charger les produits populaires (pour la page d'accueil)
async function loadPopularProducts() {
    const container = document.getElementById('popular-products');
    if (!container) return;

    try {
        const products = await getProducts({ limit: 3 });
        displayProducts(products, 'popular-products');
    } catch (error) {
        console.error('Erreur lors du chargement des produits populaires:', error);
        container.innerHTML = '<p class="empty-state">Aucun produit disponible pour le moment.</p>';
    }
}

// Afficher un message de chargement
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="loading">Chargement...</div>';
    }
}

// Afficher un état vide
function showEmptyState(containerId, message = 'Aucun élément trouvé') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>${message}</h3>
                <p>Essayez de modifier vos critères de recherche.</p>
            </div>
        `;
    }
}