(function() {
  console.log('[geo.js] chargé');
  const $ = (sel) => document.querySelector(sel);
  let map = null;
  let markers = [];

  function setStatus(msg, isError=false) {
    const el = $('#status');
    if (!el) return;
    el.textContent = msg;
    el.style.color = isError ? '#b00020' : '#666';
  }

  function ensureMap(lat, lng) {
    const mapEl = $('#map');
    if (!mapEl) return;
    if (typeof google === 'undefined' || !google.maps) {
      // Script pas encore chargé: réessayer bientôt
      setTimeout(() => ensureMap(lat, lng), 400);
      return;
    }
    if (!map) {
      map = new google.maps.Map(mapEl, {
        center: { lat, lng },
        zoom: 13,
        mapTypeControl: false,
        streetViewControl: false,
      });
      new google.maps.Marker({ position: { lat, lng }, map, title: 'Vous êtes ici' });
    } else {
      map.setCenter({ lat, lng });
    }
  }

  function clearMarkers() {
    markers.forEach(m => m.setMap && m.setMap(null));
    markers = [];
  }

  function addMarker(item) {
    if (typeof google === 'undefined' || !google.maps || !map) return;
    const m = new google.maps.Marker({
      position: { lat: parseFloat(item.latitude), lng: parseFloat(item.longitude) },
      map,
      title: item.nom || 'Magasin',
    });
    const info = new google.maps.InfoWindow({
      content: `<div><strong>${item.nom || 'Magasin'}</strong><br/>`+
               `${item.distance_km ? `Distance: ${Number(item.distance_km).toFixed(2)} km<br/>` : ''}`+
               `${item.duration_min ? `Durée: ${Number(item.duration_min).toFixed(0)} min<br/>` : ''}`+
               `${item.adresse ? `${item.adresse}<br/>` : ''}`+
               `</div>`
    });
    m.addListener('click', () => info.open({ map, anchor: m }));
    markers.push(m);
  }

  function cardHTML(item) {
    const name = item.nom || 'Magasin';
    const distance = typeof item.distance_km === 'number' ? `${item.distance_km.toFixed(2)} km` : (item.distance_km || 'N/A');
    const duration = typeof item.duration_min === 'number' ? `${item.duration_min.toFixed(0)} min` : null;
    const address = item.adresse || '';
    const rating = (typeof item.rating === 'number') ? `${item.rating.toFixed(1)}★` : '';
    const avgPrice = (typeof item.avg_price === 'number') ? `${item.avg_price.toFixed(2)}` : '';
    const travelMode = ($('#mode')?.value || 'driving');
    const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(item.latitude + ',' + item.longitude)}&travelmode=${encodeURIComponent(travelMode)}`;
    return `
      <div class="card">
        <div class="card-body">
          <h3 class="card-title">${name}</h3>
          <div class="card-meta">
            <span>Distance: ${distance}</span>
            ${duration ? `<span> • Durée: ${duration}</span>` : ''}
            ${rating ? `<span> • Note: ${rating}</span>` : ''}
            ${avgPrice ? `<span> • Prix moy.: ${avgPrice}</span>` : ''}
          </div>
          ${address ? `<div class="card-sub">${address}</div>` : ''}
          <div class="card-actions" style="margin-top:8px;">
            <a class="btn" href="${directionsUrl}" target="_blank" rel="noopener">Itinéraire</a>
          </div>
        </div>
      </div>
    `;
  }

  async function postUpdateLocation(lat, lng, radiusKm) {
    try {
      await fetch('/api/utilisateurs/utilisateurs/update_location/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude: lat, longitude: lng, rayon_km: radiusKm })
      });
    } catch (_) { /* ignore auth errors */ }
  }

  async function loadNearby(lat, lng) {
    const radiusKm = parseFloat($('#radius-km')?.value || '10') || 10;
    const mode = $('#mode')?.value || 'driving';
    ensureMap(lat, lng);
    const cb = Date.now();
    const url = `/api/magasins/magasins/proximite/?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}&rayon_km=${encodeURIComponent(radiusKm)}&mode=${encodeURIComponent(mode)}&cb=${cb}`;
    console.log('[geo] Fetch proximité:', url);
    setStatus('Recherche des magasins proches…');
    try {
      const res = await fetch(url, { cache: 'no-store', headers: { 'Cache-Control': 'no-cache' } });
      if (!res.ok) throw new Error(`Erreur API (${res.status})`);
      const data = await res.json();
      console.log('[geo] Résultats proximité:', data);
      const listEl = $('#results');
      listEl.innerHTML = '';
      clearMarkers();
      if (!data.results || data.results.length === 0) {
        setStatus('Aucun magasin trouvé dans ce rayon.');
        return;
      }
      setStatus(`${data.count} magasin(s) trouvé(s).`);
      const html = data.results.map(cardHTML).join('');
      listEl.innerHTML = html;
      data.results.forEach(addMarker);
      // Persist last location for authenticated users
      postUpdateLocation(lat, lng, radiusKm);
    } catch (e) {
      console.error(e);
      setStatus('Erreur lors du chargement des magasins proches.', true);
    }
  }

  function tryFromInputsOrError() {
    const latVal = $('#lat-input')?.value;
    const lngVal = $('#lng-input')?.value;
    const lat = parseFloat(latVal);
    const lng = parseFloat(lngVal);
    if (!isNaN(lat) && !isNaN(lng)) {
      setStatus('Recherche à partir des coordonnées saisies…');
      loadNearby(lat, lng);
    } else {
      setStatus("Impossible d'obtenir la position. Autorisez la géolocalisation ou saisissez latitude/longitude, puis cliquez sur Rechercher.", true);
    }
  }

  function getBrowserLocation() {
    if (!('geolocation' in navigator)) {
      setStatus("La géolocalisation n'est pas supportée par votre navigateur. Veuillez saisir latitude/longitude.", true);
      return;
    }
    setStatus('Obtention de votre position…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        // Prefill inputs
        if ($('#lat-input')) $('#lat-input').value = latitude.toFixed(6);
        if ($('#lng-input')) $('#lng-input').value = longitude.toFixed(6);
        loadNearby(latitude, longitude);
      },
      (err) => {
        console.warn(err);
        tryFromInputsOrError();
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('#refresh-btn')?.addEventListener('click', () => {
      const latVal = $('#lat-input')?.value;
      const lngVal = $('#lng-input')?.value;
      if (latVal && lngVal) {
        const lat = parseFloat(latVal), lng = parseFloat(lngVal);
        if (!isNaN(lat) && !isNaN(lng)) {
          setStatus('Recherche…');
          return loadNearby(lat, lng);
        }
      }
      getBrowserLocation();
    });
    // Auto-trigger on load
    getBrowserLocation();
  });
})();
