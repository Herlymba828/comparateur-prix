// Gestion de la recherche et des filtres
document.addEventListener('DOMContentLoaded', function () {
    initSearch();
    initProductFilters();
});

// Initialiser la recherche
function initSearch() {
    const searchInput = document.querySelector('.search-bar input');
    const searchButton = document.querySelector('.search-bar button');
    let autocompleteContainer = null;

    if (searchInput && searchButton) {
        searchButton.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });

        // Autocomplétion en temps réel (debounce)
        const debounced = debounce(async () => {
            const q = searchInput.value.trim();
            if (!q) {
                clearAutocomplete();
                return;
            }
            try {
                const suggestions = await autocompleteProducts(q);
                renderAutocomplete(suggestions, (sel) => {
                    // Sur sélection, aller sur produits avec q
                    window.location.href = `/produits/?search=${encodeURIComponent(sel.label)}`;
                });
            } catch (err) {
                console.error('Autocomplete error:', err);
                clearAutocomplete();
            }
        }, 250);

        searchInput.addEventListener('input', debounced);
        document.addEventListener('click', (e) => {
            if (!autocompleteContainer) return;
            if (!autocompleteContainer.contains(e.target) && e.target !== searchInput) {
                clearAutocomplete();
            }
        });
    }

    // Vérifier s'il y a un paramètre de recherche dans l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchTerm = urlParams.get('search');

    if (searchTerm && document.getElementById('products-container')) {
        // Si on est sur la page produits avec un terme de recherche
        document.getElementById('category-filter').value = '';
        document.getElementById('price-filter').value = '';
        document.getElementById('store-filter').value = '';

        loadProducts({ search: searchTerm });

        // Mettre à jour la barre de recherche si elle existe
        if (searchInput) {
            searchInput.value = searchTerm;
        }
    }

    // Fonctions internes pour autocomplétion
    function ensureAutocompleteContainer() {
        if (autocompleteContainer) return autocompleteContainer;
        const bar = document.querySelector('.search-bar');
        if (!bar) return null;
        autocompleteContainer = document.createElement('div');
        autocompleteContainer.className = 'autocomplete-list';
        bar.appendChild(autocompleteContainer);
        return autocompleteContainer;
    }

    function renderAutocomplete(items, onSelect) {
        const c = ensureAutocompleteContainer();
        if (!c) return;
        if (!items || items.length === 0) {
            c.innerHTML = '';
            c.style.display = 'none';
            return;
        }
        c.innerHTML = items.map(i => `<div class="autocomplete-item" data-id="${i.id}">${i.label}</div>`).join('');
        c.style.display = 'block';
        c.querySelectorAll('.autocomplete-item').forEach(el => {
            el.addEventListener('click', () => {
                const label = el.textContent;
                clearAutocomplete();
                onSelect({ id: el.getAttribute('data-id'), label });
            });
        });
    }

    function clearAutocomplete() {
        if (autocompleteContainer) {
            autocompleteContainer.innerHTML = '';
            autocompleteContainer.style.display = 'none';
        }
    }
}

// Initialiser les filtres de produits
function initProductFilters() {
    const categoryFilter = document.getElementById('category-filter');
    const priceFilter = document.getElementById('price-filter');
    const storeFilter = document.getElementById('store-filter');
    const searchInput = document.querySelector('.search-bar input');

    if (categoryFilter && priceFilter && storeFilter) {
        categoryFilter.addEventListener('change', applyFilters);
        priceFilter.addEventListener('change', applyFilters);
        storeFilter.addEventListener('change', applyFilters);

        // Charger les produits initiaux (sans filtres ou avec ceux de l'URL)
        const urlParams = new URLSearchParams(window.location.search);
        const searchTerm = urlParams.get('search');

        if (searchTerm) {
            loadProducts({ search: searchTerm });
        } else {
            loadProducts();
        }

        // Si on est sur la page produits, filtrer en direct pendant la saisie
        if (searchInput && window.location.pathname.startsWith('/produits/')) {
            const liveDebounced = debounce(() => {
                const term = searchInput.value.trim();
                if (term) {
                    loadProducts({ search: term });
                    const params = new URLSearchParams(window.location.search);
                    params.set('search', term);
                    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
                } else {
                    loadProducts();
                    const params = new URLSearchParams(window.location.search);
                    params.delete('search');
                    const qs = params.toString();
                    window.history.replaceState({}, '', qs ? `${window.location.pathname}?${qs}` : window.location.pathname);
                }
            }, 300);
            searchInput.addEventListener('input', liveDebounced);
        }
    }
}

// Appliquer les filtres
function applyFilters() {
    const category = document.getElementById('category-filter').value;
    const priceRange = document.getElementById('price-filter').value;
    const store = document.getElementById('store-filter').value;

    const filters = {};

    if (category) filters.category = category;
    if (priceRange) filters.priceRange = priceRange; // côté API, non utilisé pour l'instant
    if (store) filters.store = store; // mappé vers marque

    // Vérifier s'il y a un terme de recherche dans l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchTerm = urlParams.get('search');

    if (searchTerm) {
        filters.search = searchTerm;
    }

    loadProducts(filters);
}

// Effectuer une recherche
function performSearch() {
    const searchInput = document.querySelector('.search-bar input');
    const searchTerm = searchInput ? searchInput.value.trim() : '';

    if (searchTerm) {
        // Rediriger vers la page produits avec le terme de recherche
        window.location.href = `/produits/?search=${encodeURIComponent(searchTerm)}`;
    }
}

// Réinitialiser les filtres
function resetFilters() {
    document.getElementById('category-filter').value = '';
    document.getElementById('price-filter').value = '';
    document.getElementById('store-filter').value = '';

    loadProducts();
}

// Utilitaire: debounce
function debounce(fn, delay = 300) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(null, args), delay);
    };
}