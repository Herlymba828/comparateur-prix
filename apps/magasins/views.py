from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Avg
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Region, Ville, Magasin
from .serializers import SerialiseurRegion, SerialiseurVille, SerialiseurMagasin
from .filters import RegionFilter, VilleFilter, MagasinFilter


class VueEnsembleRegion(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = SerialiseurRegion
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RegionFilter
    search_fields = ["nom"]
    ordering_fields = ["nom", "id"]
    ordering = ["nom"]


class VueEnsembleVille(viewsets.ModelViewSet):
    queryset = Ville.objects.select_related('region').all()
    serializer_class = SerialiseurVille
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = VilleFilter
    search_fields = ["nom", "region__nom"]
    ordering_fields = ["nom", "id", "region__nom"]
    ordering = ["nom"]


class VueEnsembleMagasin(viewsets.ModelViewSet):
    queryset = Magasin.objects.select_related('ville', 'ville__region').all()
    serializer_class = SerialiseurMagasin
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MagasinFilter
    search_fields = ["nom", "type", "ville__nom", "ville__region__nom", "adresse", "slug"]
    ordering_fields = ["nom", "id", "type", "actif", "date_creation", "date_modification", "ville__nom", "ville__region__nom"]
    ordering = ["nom"]

    @action(detail=False, methods=["get"], url_path="proximite")
    def proximite(self, request):
        """Retourne les magasins à proximité d'une position (lat,lng), triés par distance.

        Query params:
          - lat (float), lng (float) [obligatoire]
          - rayon_km (float) défaut 10
          - max_results (int) défaut 50
          - mode (driving|walking|bicycling|transit) pour Distance Matrix (optionnel)
        """
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({"detail": "Paramètres lat et lng requis (float)."}, status=400)

        try:
            rayon_km = float(request.query_params.get('rayon_km', 10))
        except ValueError:
            rayon_km = 10.0
        try:
            max_results = int(request.query_params.get('max_results', 50))
        except ValueError:
            max_results = 50
        mode = request.query_params.get('mode') or 'driving'

        # Haversine helper
        from math import radians, sin, cos, sqrt, atan2
        def haversine_km(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c

        # Bounding box simple pour réduire les candidats (~approx)
        lat_delta = rayon_km / 111.0
        lng_delta = rayon_km / max(0.0001, (111.320 * cos(radians(lat))))

        qs = (self.get_queryset()
              .annotate(avg_price=Avg('prix__prix_actuel'))
              .filter(latitude__isnull=False, longitude__isnull=False,
                      latitude__gte=lat - lat_delta, latitude__lte=lat + lat_delta,
                      longitude__gte=lng - lng_delta, longitude__lte=lng + lng_delta))

        candidats = []
        for m in qs:
            try:
                d = haversine_km(float(m.latitude), float(m.longitude), lat, lng)
            except Exception:
                continue
            if d <= rayon_km:
                m.distance_km = d
                # Signals
                rating = getattr(m, 'rating', None)
                avg_price = getattr(m, 'avg_price', None)
                # Simple normalization
                inv_dist = 1.0 / (1.0 + d)
                rating_term = (float(rating) / 5.0) if isinstance(rating, (int, float)) else 0.0
                price_term = 1.0 / (1.0 + (float(avg_price) / 100.0)) if isinstance(avg_price, (int, float)) else 0.0
                # Weighted score
                m.score = 0.6 * inv_dist + 0.3 * rating_term + 0.1 * price_term
                candidats.append(m)

        candidats.sort(key=lambda x: getattr(x, 'distance_km', 1e9))
        candidats = candidats[:max(1, min(max_results, 200))]

        # Optionnel: Google Distance Matrix pour durée
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if api_key:
            try:
                import googlemaps
                gmaps = googlemaps.Client(key=api_key)
                origins = [(lat, lng)]
                destinations = [(float(m.latitude), float(m.longitude)) for m in candidats]
                dm = gmaps.distance_matrix(origins=origins, destinations=destinations, mode=mode)
                rows = dm.get('rows', [])
                if rows and rows[0].get('elements'):
                    for m, el in zip(candidats, rows[0]['elements']):
                        if el.get('status') == 'OK':
                            dur = el['duration']['value'] / 60.0  # seconds -> minutes
                            m.duration_min = dur
                            # ajuster score en tenant compte du temps
                            m.score = (m.score or 0) + 1.0 / (1.0 + dur/10.0)
            except Exception:
                # Si l'appel échoue, on ignore la durée
                pass

        serializer = self.get_serializer(candidats, many=True)
        return Response({
            'count': len(candidats),
            'params': {
                'lat': lat, 'lng': lng, 'rayon_km': rayon_km, 'mode': mode, 'max_results': max_results
            },
            'results': serializer.data,
        })
