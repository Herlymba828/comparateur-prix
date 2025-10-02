// Helpers AJAX
const API_BASE = '/api';

async function fetchJSON(path, params = {}) {
    const url = new URL(path, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
    });
    const resp = await fetch(url.toString(), { headers: { 'Accept': 'application/json' } });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
}

// Autocomplétion produits (API de recherche dédiée)
async function autocompleteProducts(query) {
    if (!query || !query.trim()) return [];
    const data = await fetchJSON(`${API_BASE}/search/autocomplete/`, { q: query.trim() });
    const items = data.results || [];
    return items.map(i => ({ id: i.id, label: i.label }));
}

// Récupérer tous les produits avec filtres
async function getProducts(filters = {}) {
    // Map front filters -> API params
    const params = {};
    if (filters.category) params.categorie = filters.category;
    if (filters.store) params.marque = filters.store; // approximation: using marque as store-like filter
    if (filters.limit) params.page_size = filters.limit;

    // Si une recherche texte est fournie, utiliser l'API de recherche dédiée
    if (filters.search && String(filters.search).trim()) {
        const q = String(filters.search).trim();
        const data = await fetchJSON(`${API_BASE}/search/produits/`, { q, ...params });
        const items = data.results || [];
        return items.map(p => ({
            id: p.id,
            name: p.nom,
            description: p.categorie_nom ? `Catégorie: ${p.categorie_nom}` : '',
            image: 'https://via.placeholder.com/300x200?text=Produit',
            price: p.min_prix !== null && p.min_prix !== undefined ? Number(p.min_prix) : undefined,
            rating: undefined,
            store: p.marque || (p.categorie_nom || ''),
            currency: p.devise || 'XAF',
        }));
    }

    // Sinon, listing classique via l'app produits
    const data = await fetchJSON(`${API_BASE}/produits/produits/`, params);
    // DRF pagination returns {results: []} else list
    const items = Array.isArray(data) ? data : (data.results || []);
    return items.map(p => ({
        id: p.id,
        name: p.nom,
        description: p.description || '',
        image: 'https://via.placeholder.com/300x200?text=Produit',
        price: undefined,
        rating: undefined,
        store: p.marque || (p.categorie_nom || ''),
    }));
}

// Récupérer tous les magasins
async function getStores() {
    const data = await fetchJSON(`${API_BASE}/magasins/magasins/`, {});
    const items = Array.isArray(data) ? data : (data.results || []);
    return items.map(m => ({
        id: m.id,
        name: m.nom,
        logo: 'https://via.placeholder.com/150x80?text=Magasin',
        rating: m.actif ? 4.3 : 3.9,
        productsCount: undefined,
        location: m.ville?.nom || '',
    }));
}

// Récupérer les recommandations (avec métadonnées de pagination)
async function fetchRecommendations(params = {}) {
    const data = await fetchJSON(`${API_BASE}/recommandations/produits/`, params);
    const items = (data.results || []).map(r => ({
        id: r.produit_id,
        name: r.produit_nom,
        description: `${r.magasin_nom} · ${r.valeur} ${r.devise}`,
        image: 'https://via.placeholder.com/300x200?text=Reco',
        price: Number(r.valeur || 0),
        rating: undefined,
        store: r.magasin_nom,
    }));
    const meta = {
        count: data.count,
        page: data.page,
        page_size: data.page_size,
        total_pages: data.total_pages,
        next_page: data.next_page,
    };
    return { items, meta };
}

// Afficher les produits dans le DOM
function displayProducts(products, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!products || products.length === 0) {
        container.innerHTML = '<div class="empty-state">Aucun produit trouvé</div>';
        return;
    }

    container.innerHTML = products.map(product => `
        <div class="product-card">
            <img src="${product.image}" alt="${product.name}">
            <h3>${product.name}</h3>
            <p class="description">${product.description || ''}</p>
            ${product.price !== undefined ? `<div class="price">${Number(product.price).toFixed(2)}€</div>` : ''}
            ${product.rating !== undefined ? `<div class="rating">⭐ ${product.rating}</div>` : ''}
            ${product.store ? `<p class="store">${product.store}</p>` : ''}
            <button class="btn">Voir détails</button>
        </div>
    `).join('');
}

// Afficher les magasins dans le DOM
function displayStores(stores, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!stores || stores.length === 0) {
        container.innerHTML = '<div class="empty-state">Aucun magasin trouvé</div>';
        return;
    }

    container.innerHTML = stores.map(store => `
        <div class="store-card">
            <img src="${store.logo}" alt="${store.name}" style="height: 80px; object-fit: contain;">
            <h3>${store.name}</h3>
            ${store.rating ? `<div class="rating">⭐ ${store.rating}</div>` : ''}
            ${store.productsCount ? `<p>${store.productsCount} produits</p>` : ''}
            ${store.location ? `<p>Localisation: ${store.location}</p>` : ''}
            <button class="btn">Voir les produits</button>
        </div>
    `).join('');
}

// Charger les produits avec filtres
async function loadProducts(filters = {}) {
    const container = document.getElementById('products-container');
    if (!container) return;

    showLoading('products-container');

    try {
        const products = await getProducts(filters);
        displayProducts(products, 'products-container');
    } catch (error) {
        console.error('Erreur lors du chargement des produits:', error);
        showEmptyState('products-container', 'Erreur de chargement');
    }
}

// Charger les magasins
async function loadStores() {
    const container = document.getElementById('stores-container');
    if (!container) return;

    showLoading('stores-container');

    try {
        const stores = await getStores();
        displayStores(stores, 'stores-container');
    } catch (error) {
        console.error('Erreur lors du chargement des magasins:', error);
        showEmptyState('stores-container', 'Erreur de chargement');
    }
}

// Charger les recommandations
async function loadRecommendations() {
    const container = document.getElementById('recommendations-container');
    if (!container) return;

    showLoading('recommendations-container');

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const params = Object.fromEntries(urlParams.entries());
        // valeurs par défaut
        if (!params.page_size) params.page_size = 12;
        const { items, meta } = await fetchRecommendations(params);
        displayProducts(items, 'recommendations-container');
        renderPagination(meta, 'reco-pagination');
    } catch (error) {
        console.error('Erreur lors du chargement des recommandations:', error);
        showEmptyState('recommendations-container', 'Erreur de chargement');
        renderPagination({ count: 0, page: 1, total_pages: 1 }, 'reco-pagination');
    }
}

function renderPagination(meta, containerId) {
    const c = document.getElementById(containerId);
    if (!c) return;
    const page = Number(meta.page || 1);
    const total = Number(meta.total_pages || 1);
    if (total <= 1) { c.innerHTML = ''; return; }
    const prevPage = page > 1 ? page - 1 : null;
    const nextPage = page < total ? page + 1 : null;
    c.innerHTML = `
        <div class="pagination">
            <button class="btn" ${prevPage ? '' : 'disabled'} data-page="${prevPage || ''}">Précédent</button>
            <span>Page ${page} / ${total}</span>
            <button class="btn" ${nextPage ? '' : 'disabled'} data-page="${nextPage || ''}">Suivant</button>
        </div>
    `;
    c.querySelectorAll('button[data-page]')
        .forEach(btn => btn.addEventListener('click', () => {
            const p = btn.getAttribute('data-page');
            if (!p) return;
            const params = new URLSearchParams(window.location.search);
            params.set('page', p);
            window.location.search = params.toString();
        }));
}

// Charger les analyses (placeholder)
async function loadAnalytics() {
    // Cette fonction serait connectée à une API réelle
    console.log('Chargement des données analytiques...');
}