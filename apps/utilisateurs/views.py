from rest_framework import status, viewsets, permissions

from rest_framework.decorators import action
from rest_framework.response import Response
try:
    from rest_framework_simplejwt.tokens import RefreshToken
    HAS_JWT = True
except Exception:  # ModuleNotFoundError or others
    RefreshToken = None
    HAS_JWT = False

from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from decimal import Decimal
import io
import base64
import qrcode
from django.utils.dateparse import parse_datetime

from .models import Utilisateur, ProfilUtilisateur, Abonnement, HistoriqueConnexion, HistoriqueRemises
from .utils import generer_token_activation, verifier_token_activation, generer_token_reset, verifier_token_reset
from .tasks import send_activation_email, send_reset_email
from .serializers import (
    InscriptionSerializer, ConnexionSerializer, UtilisateurSerializer,
    MiseAJourUtilisateurSerializer, ProfilUtilisateurSerializer,
    AbonnementSerializer, ChangementMotDePasseSerializer, 
    UtilisateurLightSerializer, HistoriqueRemisesSerializer,
    ApplicationRemiseSerializer, StatistiquesFideliteSerializer,
    HistoriqueConnexionSerializer
)
from apps.utilisateurs.permissions import IsProprietaireProfil, IsAdminOrReadOnly, IsAdminOrModerator, IsSuperUser
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import devices_for_user

class UtilisateurViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des utilisateurs avec système de fidélité"""
    
    queryset = Utilisateur.objects.select_related('profil').prefetch_related(
        'profil__magasins_preferes', 'profil__categories_preferees_remises'
    )
    serializer_class = UtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrage personnalisé selon les permissions"""
        if self.request.user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(id=self.request.user.id)
    
    def get_serializer_class(self):
        """Utiliser différents serializers selon l'action"""
        if self.action == 'list':
            return UtilisateurLightSerializer
        elif self.action == 'create':
            return InscriptionSerializer
        elif self.action in ['update', 'partial_update']:
            return MiseAJourUtilisateurSerializer
        return self.serializer_class
    
    @action(detail=False, methods=['get'])
    def moi(self, request):
        """Endpoint pour récupérer l'utilisateur connecté"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def inscrire(self, request):
        """Inscription d'un nouvel utilisateur"""
        serializer = InscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            utilisateur = serializer.save()
            # Rendre le compte inactif jusqu'à activation email
            utilisateur.is_active = False
            utilisateur.est_verifie = False
            utilisateur.save(update_fields=['is_active', 'est_verifie'])
            
            # Créer le profil utilisateur
            ProfilUtilisateur.objects.create(utilisateur=utilisateur)
            
            # Créer un abonnement gratuit par défaut
            Abonnement.objects.create(
                utilisateur=utilisateur,
                date_fin=timezone.now() + timedelta(days=365*10)
            )
            # Générer et envoyer le lien d'activation
            token = generer_token_activation(utilisateur.id, utilisateur.email)
            send_activation_email.delay(utilisateur.email, token)
        
        # Générer le token JWT si disponible
        data = {
            'utilisateur': UtilisateurSerializer(utilisateur).data,
        }
        if HAS_JWT and RefreshToken is not None:
            refresh = RefreshToken.for_user(utilisateur)
            data.update({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def connecter(self, request):
        """Authentifie un utilisateur via username ou email. Retourne des tokens JWT si dispo.

        Body JSON: { username?: str, email?: str, password: str }
        """
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if not password or (not username and not email):
            return Response({'detail': 'username ou email et password requis.'}, status=400)
        # Si email fourni, le convertir en username
        if not username and email:
            try:
                u = Utilisateur.objects.get(email=email)
                username = u.username
            except Utilisateur.DoesNotExist:
                return Response({'detail': 'Identifiants invalides.'}, status=401)
        user = authenticate(request=request, username=username, password=password)
        if not user:
            # log tentative
            try:
                HistoriqueConnexion.objects.create(
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    reussi=False,
                    utilisateur=Utilisateur.objects.filter(username=username).first()
                )
            except Exception:
                pass
            return Response({'detail': 'Identifiants invalides.'}, status=401)
        if not user.is_active:
            return Response({'detail': 'Compte inactif. Veuillez activer votre compte.'}, status=403)
        # Créer la session
        try:
            login(request, user)
        except Exception:
            pass
        # Log réussite
        try:
            HistoriqueConnexion.objects.create(
                utilisateur=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                reussi=True,
            )
        except Exception:
            pass
        payload = {'utilisateur': UtilisateurSerializer(user).data}
        if HAS_JWT and RefreshToken is not None:
            refresh = RefreshToken.for_user(user)
            payload.update({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(payload)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def changer_mot_de_passe(self, request):
        """Change le mot de passe de l'utilisateur authentifié.

        Body JSON attendu: {
          "ancien_mot_de_passe": str,
          "nouveau_mot_de_passe": str,
          "confirmation_mot_de_passe": str
        }
        """
        serializer = ChangementMotDePasseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ancien = serializer.validated_data['ancien_mot_de_passe']
        nouveau = serializer.validated_data['nouveau_mot_de_passe']

        user = request.user
        # Vérifier l'ancien mot de passe
        if not user.check_password(ancien):
            return Response({'ancien_mot_de_passe': 'Ancien mot de passe incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(nouveau)
        user.save(update_fields=['password'])
        return Response({'detail': 'Mot de passe mis à jour.'})

    @action(detail=False, methods=['get'])
    def statistiques_fidelite(self, request):
        """Statistiques fidélité enrichies (fidélité + abonnement + progression)."""
        user = request.user
        total_achats = getattr(user, 'total_achats', Decimal('0.00')) or Decimal('0.00')
        niveau = getattr(user, 'niveau_fidelite', 1) or 1
        base_pct = Decimal(str(user.pourcentage_remise_fidelite or 0))
        # Abonnement
        abo_pct = Decimal('0')
        abo = getattr(user, 'abonnement', None)
        if abo and getattr(abo, 'est_valide', False):
            try:
                if abo.est_valide:
                    abo_pct = Decimal(str(abo.remise_supplementaire or 0))
            except Exception:
                pass
        total_pct = base_pct + abo_pct
        # Progression vers prochain niveau selon _mettre_a_jour_niveau_fidelite
        thresholds = [Decimal('0'), Decimal('50'), Decimal('200'), Decimal('500'), Decimal('1000')]
        # niveaux 1..5 -> prochain seuil indexé
        if niveau >= 5:
            prochain_seuil = None
            progression = Decimal('100.0')
        else:
            prochain_seuil = thresholds[niveau] if 1 <= niveau < 5 else Decimal('50')
            # base du niveau courant
            base_seuil = thresholds[niveau-1] if 2 <= niveau <= 5 else Decimal('0')
            # progression sur l'intervalle [base_seuil, prochain_seuil]
            intervalle = (prochain_seuil - base_seuil) or Decimal('1')
            progression = max(Decimal('0.0'), min(Decimal('100.0'), ((total_achats - base_seuil) * Decimal('100.0')) / intervalle))
        # Jours depuis le dernier achat
        last_days = None
        try:
            if user.date_dernier_achat:
                delta = timezone.now() - user.date_dernier_achat
                last_days = delta.days
        except Exception:
            last_days = None
        payload = {
            'points_fidelite': int(getattr(user, 'points_fidelite', 0) or 0),
            'niveau_fidelite': int(niveau),
            'pourcentage_remise': str(total_pct),
            'pourcentage_remise_fidelite': str(base_pct),
            'pourcentage_remise_abonnement': str(abo_pct),
            'total_achats': str(total_achats),
            'nombre_commandes': int(getattr(user, 'nombre_commandes', 0) or 0),
            'est_client_fidele': bool(getattr(user, 'est_client_fidele', False)),
            'prochain_niveau_seuil': None if prochain_seuil is None else str(prochain_seuil),
            'progression_niveau': float(progression),
            'derniere_commande_jours': last_days,
        }
        s = StatistiquesFideliteSerializer(data=payload)
        s.is_valid(raise_exception=True)
        return Response(s.data)

    @action(detail=False, methods=['get'])
    def historique_remises(self, request):
        """Liste (éventuelle) des remises appliquées liées à l'utilisateur courant."""
        try:
            qs = HistoriqueRemises.objects.filter(utilisateur=request.user)
        except Exception:
            qs = HistoriqueRemises.objects.none()
        data = HistoriqueRemisesSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})

    @action(detail=False, methods=['post'])
    def appliquer_remise(self, request):
        """Applique une remise combinée (fidélité + catégorie + abonnement) et journalise."""
        s = ApplicationRemiseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        produit = s.validated_data['produit']
        prix_original = Decimal(str(s.validated_data['prix_original']))
        user = request.user
        # Composantes de remise
        base_pct = Decimal(str(user.pourcentage_remise_fidelite or 0))
        # Bonus catégorie si le produit a une catégorie
        categorie = getattr(produit, 'categorie', None)
        try:
            cat_bonus = Decimal(str(user._get_remise_categorie(categorie)))  # basé sur la logique du modèle
        except Exception:
            cat_bonus = Decimal('0')
        abo_bonus = Decimal('0')
        abo = getattr(user, 'abonnement', None)
        try:
            if abo and abo.est_valide:
                abo_bonus = Decimal(str(abo.remise_supplementaire or 0))
        except Exception:
            pass
        total_pct = base_pct + cat_bonus + abo_bonus
        # garde-fous
        if total_pct < 0:
            total_pct = Decimal('0')
        if total_pct > 50:
            total_pct = Decimal('50')
        montant = (prix_original * total_pct) / Decimal('100')
        prix_remise = prix_original - montant
        # Déterminer le type
        comp_fidelite = (base_pct > 0 or cat_bonus > 0)
        comp_abo = (abo_bonus > 0)
        if comp_fidelite and comp_abo:
            type_remise = 'combinee'
        elif comp_abo:
            type_remise = 'abonnement'
        elif comp_fidelite:
            type_remise = 'fidelite'
        else:
            type_remise = 'promotion'
        # Journaliser
        try:
            HistoriqueRemises.objects.create(
                utilisateur=user,
                produit=produit,
                prix_original=prix_original,
                prix_remise=prix_remise,
                pourcentage_remise=total_pct,
                montant_economise=montant,
                type_remise=type_remise,
            )
        except Exception:
            pass
        return Response({
            'produit_id': produit.id,
            'prix_original': str(prix_original),
            'prix_remise': str(prix_remise),
            'pourcentage_remise': str(total_pct),
            'montant_economise': str(montant),
            'components': {
                'fidelite_pct': str(base_pct),
                'categorie_pct': str(cat_bonus),
                'abonnement_pct': str(abo_bonus),
            },
            'type_remise': type_remise,
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_location(self, request):
        """Met à jour la position courante de l'utilisateur sans modifier le schéma.

        Body JSON: { "latitude": float, "longitude": float, "rayon_km": int? }
        Stocke dans profil.preferences_recherche: { last_location: {lat, lng, at}, rayon_km }
        """
        try:
            lat = float(request.data.get('latitude'))
            lng = float(request.data.get('longitude'))
        except (TypeError, ValueError):
            return Response({'detail': 'latitude et longitude requis (float).'}, status=400)

        rayon_km = request.data.get('rayon_km')
        try:
            rayon_km = int(rayon_km) if rayon_km is not None else None
        except (TypeError, ValueError):
            rayon_km = None

        # Upsert in preferences_recherche
        profil = getattr(request.user, 'profil', None)
        if profil is None:
            profil = ProfilUtilisateur.objects.create(utilisateur=request.user)
        prefs = dict(profil.preferences_recherche or {})
        prefs['last_location'] = {
            'lat': lat,
            'lng': lng,
            'at': timezone.now().isoformat(),
        }
        if rayon_km is not None and rayon_km > 0:
            profil.rayon_recherche_km = rayon_km
        profil.preferences_recherche = prefs
        profil.save(update_fields=['preferences_recherche', 'rayon_recherche_km'])

        # Persist also on Utilisateur (dedicated fields)
        user = request.user
        user.latitude = lat
        user.longitude = lng
        user.last_location_at = timezone.now()
        user.save(update_fields=['latitude', 'longitude', 'last_location_at'])

        return Response({'ok': True, 'last_location': prefs['last_location'], 'rayon_km': profil.rayon_recherche_km})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def renvoyer_activation(self, request):
        """Renvoyer un email d'activation si le compte n'est pas encore vérifié."""
        utilisateur = request.user
        if utilisateur.est_verifie:
            return Response({'detail': "Compte déjà vérifié."}, status=status.HTTP_400_BAD_REQUEST)
        token = generer_token_activation(utilisateur.id, utilisateur.email)
        send_activation_email.delay(utilisateur.email, token)
        return Response({'detail': "Email d'activation renvoyé."})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsAdminOrModerator])
    def roles(self, request):
        """Liste des rôles disponibles et des membres par rôle (admin/modérateur seulement)."""
        roles = {}
        for name in ["admin", "moderateur", "premium"]:
            grp, _ = Group.objects.get_or_create(name=name)
            roles[name] = list(grp.user_set.values_list('id', 'username'))
        return Response({'roles': roles})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminOrModerator])
    def assign_role(self, request):
        """Assigne un rôle (group) à un utilisateur. Body: {user_id, role}."""
        user_id = request.data.get('user_id')
        role = (request.data.get('role') or '').strip().lower()
        if role not in {"admin", "moderateur", "premium"}:
            return Response({'detail': 'Rôle invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        grp, _ = Group.objects.get_or_create(name=role)
        user.groups.add(grp)
        return Response({'detail': f'Rôle {role} assigné à {user.username}.'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdminOrModerator])
    def revoke_role(self, request):
        """Révoque un rôle (group) d'un utilisateur. Body: {user_id, role}."""
        user_id = request.data.get('user_id')
        role = (request.data.get('role') or '').strip().lower()
        if role not in {"admin", "moderateur", "premium"}:
            return Response({'detail': 'Rôle invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = Utilisateur.objects.get(id=user_id)
        except Utilisateur.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            grp = Group.objects.get(name=role)
        except Group.DoesNotExist:
            return Response({'detail': 'Rôle inexistant.'}, status=status.HTTP_404_NOT_FOUND)
        user.groups.remove(grp)
        return Response({'detail': f'Rôle {role} révoqué pour {user.username}.'})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def connexions(self, request):
        """Historique des connexions de l'utilisateur courant (avec filtres).
        Query params: success=true/false, since=ISO, until=ISO, limit=int (def 50)
        """
        qs = HistoriqueConnexion.objects.filter(utilisateur=request.user)
        success = request.query_params.get('success')
        if success is not None:
            val = str(success).lower() in ('1', 'true', 'yes', 'y')
            qs = qs.filter(reussi=val)
        since = request.query_params.get('since')
        if since:
            dt = parse_datetime(since)
            if dt:
                qs = qs.filter(date_connexion__gte=dt)
        until = request.query_params.get('until')
        if until:
            dt = parse_datetime(until)
            if dt:
                qs = qs.filter(date_connexion__lte=dt)
        try:
            limit = int(request.query_params.get('limit', '50'))
        except ValueError:
            limit = 50
        qs = qs.order_by('-date_connexion')[:max(1, min(limit, 500))]
        data = HistoriqueConnexionSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsAdminOrModerator])
    def connexions_all(self, request):
        """Historique global des connexions (admin/modérateur) avec filtres.
        Query params: user_id, success=true/false, since=ISO, until=ISO, limit=int (def 100)
        """
        qs = HistoriqueConnexion.objects.all()
        user_id = request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(utilisateur_id=user_id)
        success = request.query_params.get('success')
        if success is not None:
            val = str(success).lower() in ('1', 'true', 'yes', 'y')
            qs = qs.filter(reussi=val)
        since = request.query_params.get('since')
        if since:
            dt = parse_datetime(since)
            if dt:
                qs = qs.filter(date_connexion__gte=dt)
        until = request.query_params.get('until')
        if until:
            dt = parse_datetime(until)
            if dt:
                qs = qs.filter(date_connexion__lte=dt)
        try:
            limit = int(request.query_params.get('limit', '100'))
        except ValueError:
            limit = 100
        qs = qs.select_related('utilisateur').order_by('-date_connexion')[:max(1, min(limit, 1000))]
        data = HistoriqueConnexionSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def twofa_setup(self, request):
        """Crée/configure un appareil TOTP et renvoie un QR code (base64 PNG) et l'otpauth URL."""
        user = request.user
        device, _ = TOTPDevice.objects.get_or_create(user=user, name="totp-default")
        # Generate QR for device.config_url
        img = qrcode.make(device.config_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return Response({
            'otpauth_url': device.config_url,
            'qrcode_png_base64': b64
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def twofa_verify(self, request):
        """Vérifie un code TOTP et confirme l'appareil."""
        token = request.data.get('token')
        if not token:
            return Response({'detail': 'Token requis.'}, status=status.HTTP_400_BAD_REQUEST)
        for device in devices_for_user(request.user, confirmed=None):
            if device.verify_token(token):
                device.confirmed = True
                device.save(update_fields=['confirmed'])
                return Response({'detail': '2FA activée et confirmée.'})
        return Response({'detail': 'Token invalide.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def twofa_disable(self, request):
        """Désactive le 2FA en supprimant les appareils TOTP de l'utilisateur."""
        qs = TOTPDevice.objects.filter(user=request.user)
        count = qs.count()
        qs.delete()
        return Response({'detail': f'2FA désactivée. Appareils supprimés: {count}.'})

from rest_framework.decorators import api_view, permission_classes  # noqa: E402
from django.contrib.sessions.models import Session  # noqa: E402
from django.utils import timezone  # noqa: E402
from django.http import HttpResponse, HttpResponseBadRequest  # noqa: E402
try:
    from rest_framework_simplejwt.tokens import OutstandingToken, BlacklistedToken  # noqa: E402
except Exception:
    OutstandingToken = None
    BlacklistedToken = None

@api_view(["GET"]) 
@permission_classes([permissions.AllowAny])
def activer_compte(request, token: str):
    """Active le compte via un token signé envoyé par email."""
    data = verifier_token_activation(token)
    if not data:
        return Response({'detail': 'Token invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        utilisateur = Utilisateur.objects.get(id=data['uid'], email=data['email'])
    except Utilisateur.DoesNotExist:
        return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    if utilisateur.est_verifie and utilisateur.is_active:
        return Response({'detail': 'Compte déjà activé.'})
    utilisateur.est_verifie = True
    utilisateur.is_active = True
    utilisateur.save(update_fields=['est_verifie', 'is_active'])
    return Response({'detail': 'Compte activé avec succès.'})

@api_view(["GET"]) 
@permission_classes([permissions.AllowAny])
def activer_compte_query(request):
    """Variante qui accepte le token en query param: /api/auth/activation/confirmer?token=..."""
    token = request.query_params.get('token') or request.GET.get('token')
    if not token:
        return Response({'detail': 'Paramètre token requis.'}, status=status.HTTP_400_BAD_REQUEST)
    data = verifier_token_activation(token)
    if not data:
        return Response({'detail': 'Token invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        utilisateur = Utilisateur.objects.get(id=data['uid'], email=data['email'])
    except Utilisateur.DoesNotExist:
        return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    if utilisateur.est_verifie and utilisateur.is_active:
        return Response({'detail': 'Compte déjà activé.'})
    utilisateur.est_verifie = True
    utilisateur.is_active = True
    utilisateur.save(update_fields=['est_verifie', 'is_active'])
    return Response({'detail': 'Compte activé avec succès.'})

def web_activate_page(request, token: str):
    """Page d'atterrissage web pour Universal/App Links: /activate/<token>
    Active le compte puis affiche un résultat HTML minimal.
    """
    data = verifier_token_activation(token)
    if not data:
        return HttpResponseBadRequest('<h1>Activation échouée</h1><p>Token invalide ou expiré.</p>')
    try:
        utilisateur = Utilisateur.objects.get(id=data['uid'], email=data['email'])
    except Utilisateur.DoesNotExist:
        return HttpResponseBadRequest('<h1>Activation échouée</h1><p>Utilisateur introuvable.</p>')
    if not (utilisateur.est_verifie and utilisateur.is_active):
        utilisateur.est_verifie = True
        utilisateur.is_active = True
        utilisateur.save(update_fields=['est_verifie', 'is_active'])
    return HttpResponse('<h1>Activation réussie</h1><p>Votre compte est activé. Vous pouvez ouvrir l\'application et vous connecter.</p>')

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def demander_reset_mot_de_passe(request):
    """Demande de réinitialisation: envoie un email avec lien signé (toujours réponse 200)."""
    from .serializers import DemandeResetMotDePasseSerializer
    serializer = DemandeResetMotDePasseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    try:
        utilisateur = Utilisateur.objects.get(email=email)
        token = generer_token_reset(utilisateur.id, utilisateur.email)
        send_reset_email.delay(utilisateur.email, token)
    except Utilisateur.DoesNotExist:
        pass  # Ne pas révéler l'existence
    return Response({'detail': 'Si un compte existe pour cet email, un lien de réinitialisation a été envoyé.'})

@api_view(["POST"]) 
@permission_classes([permissions.AllowAny])
def confirmer_reset_mot_de_passe(request, token: str):
    """Confirme la réinitialisation via token valide et définit le nouveau mot de passe."""
    from .serializers import ConfirmationResetMotDePasseSerializer
    data_token = verifier_token_reset(token)
    if not data_token:
        return Response({'detail': 'Token invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        utilisateur = Utilisateur.objects.get(id=data_token['uid'], email=data_token['email'])
    except Utilisateur.DoesNotExist:
        return Response({'detail': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ConfirmationResetMotDePasseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    utilisateur.set_password(serializer.validated_data['nouveau_mot_de_passe'])
    utilisateur.save(update_fields=['password'])
    return Response({'detail': 'Mot de passe réinitialisé avec succès.'})

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def lister_sessions(request):
    """Liste les sessions actives de l'utilisateur courant."""
    now = timezone.now()
    sessions = []
    for s in Session.objects.filter(expire_date__gte=now):
        data = s.get_decoded()
        uid = str(request.user.id)
        if data.get('_auth_user_id') == uid:
            sessions.append({
                'session_key': s.session_key,
                'expire_date': s.expire_date,
            })
    return Response({'sessions': sessions})

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def revoquer_session(request):
    """Révoque (supprime) une session spécifique appartenant à l'utilisateur."""
    key = request.data.get('session_key')
    if not key:
        return Response({'detail': 'session_key requis.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        s = Session.objects.get(session_key=key)
        data = s.get_decoded()
        if data.get('_auth_user_id') != str(request.user.id):
            return Response({'detail': "Session non trouvée pour cet utilisateur."}, status=status.HTTP_404_NOT_FOUND)
        s.delete()
        return Response({'detail': 'Session révoquée.'})
    except Session.DoesNotExist:
        return Response({'detail': 'Session introuvable.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_all(request):
    """Déconnecte l'utilisateur de toutes les sessions et blacklist tous ses refresh tokens (JWT)."""
    # Supprimer toutes les sessions liées
    now = timezone.now()
    for s in Session.objects.filter(expire_date__gte=now):
        data = s.get_decoded()
        if data.get('_auth_user_id') == str(request.user.id):
            s.delete()
    # Blacklister les refresh tokens si simplejwt installé
    if OutstandingToken and BlacklistedToken:
        for t in OutstandingToken.objects.filter(user=request.user):
            try:
                BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                pass
    return Response({'detail': 'Déconnecté de toutes les sessions.'})

import os  # noqa: E402
import requests  # noqa: E402
import jwt  # PyJWT
from jwt import PyJWKClient

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def google_login(request):
    """Authentifie via Google OAuth2 id_token (Sign-In with Google).

    Body: { "id_token": "..." }
    Vérifie le token via l'endpoint tokeninfo de Google, compare l'audience au GOOGLE_CLIENT_ID.
    Crée/associe un utilisateur, active et marque vérifié, puis renvoie des tokens JWT si disponibles.
    """
    id_token = request.data.get('id_token')
    if not id_token:
        return Response({'detail': 'id_token requis.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        resp = requests.get('https://oauth2.googleapis.com/tokeninfo', params={'id_token': id_token}, timeout=10)
        if resp.status_code != 200:
            return Response({'detail': 'Token Google invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        aud_ok = os.getenv('GOOGLE_CLIENT_ID')
        if aud_ok and data.get('aud') != aud_ok:
            return Response({'detail': 'Audience non autorisée.'}, status=status.HTTP_403_FORBIDDEN)
        email = data.get('email')
        if not email:
            return Response({'detail': 'Email Google manquant.'}, status=status.HTTP_400_BAD_REQUEST)
        # Créer ou récupérer l'utilisateur
        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            base_username = (email.split('@')[0])[:20] or 'user'
            candidate = base_username
            i = 1
            while Utilisateur.objects.filter(username=candidate).exists():
                candidate = f"{base_username}{i}"
                i += 1
            user = Utilisateur.objects.create_user(username=candidate, email=email)
        # Marquer actif/vérifié
        updates = []
        if not user.is_active:
            user.is_active = True
            updates.append('is_active')
        if not getattr(user, 'est_verifie', False):
            user.est_verifie = True
            updates.append('est_verifie')
        if updates:
            user.save(update_fields=updates)
        # Log connexion audit
        try:
            HistoriqueConnexion.objects.create(
                utilisateur=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                reussi=True,
            )
        except Exception:
            pass
        # Générer les tokens JWT si dispo
        payload = {'utilisateur': UtilisateurSerializer(user).data}
        if HAS_JWT and RefreshToken is not None:
            refresh = RefreshToken.for_user(user)
            payload.update({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(payload)
    except Exception as e:
        return Response({'detail': f'Erreur Google OAuth: {e}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def facebook_login(request):
    """Authentifie via Facebook OAuth2 access_token.

    Body: { "access_token": "..." }
    Vérifie le token via debug_token si APP credentials présents, sinon récupère email via /me.
    """
    access_token = request.data.get('access_token')
    if not access_token:
        return Response({'detail': 'access_token requis.'}, status=status.HTTP_400_BAD_REQUEST)
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    try:
        if app_id and app_secret:
            app_token = f"{app_id}|{app_secret}"
            dbg = requests.get(
                'https://graph.facebook.com/debug_token',
                params={'input_token': access_token, 'access_token': app_token}, timeout=10
            ).json()
            if not dbg.get('data', {}).get('is_valid'):
                return Response({'detail': 'Token Facebook invalide.'}, status=status.HTTP_400_BAD_REQUEST)
            if dbg['data'].get('app_id') and dbg['data']['app_id'] != app_id:
                return Response({'detail': 'App non autorisée.'}, status=status.HTTP_403_FORBIDDEN)
        me = requests.get(
            'https://graph.facebook.com/me',
            params={'fields': 'id,name,email', 'access_token': access_token}, timeout=10
        ).json()
        email = me.get('email')
        if not email:
            # fallback: construct pseudo-email if email not granted
            email = f"fb_{me.get('id')}@facebook.local"
        # Upsert user
        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            base_username = (email.split('@')[0])[:20] or 'user'
            candidate = base_username
            i = 1
            while Utilisateur.objects.filter(username=candidate).exists():
                candidate = f"{base_username}{i}"
                i += 1
            user = Utilisateur.objects.create_user(username=candidate, email=email)
        updates = []
        if not user.is_active:
            user.is_active = True; updates.append('is_active')
        if not getattr(user, 'est_verifie', False):
            user.est_verifie = True; updates.append('est_verifie')
        if updates:
            user.save(update_fields=updates)
        payload = {'utilisateur': UtilisateurSerializer(user).data}
        if HAS_JWT and RefreshToken is not None:
            refresh = RefreshToken.for_user(user)
            payload.update({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(payload)
    except Exception as e:
        return Response({'detail': f'Erreur Facebook OAuth: {e}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def apple_login(request):
    """Authentifie via Apple Sign-In id_token (JWT RS256).

    Body: { "id_token": "..." }
    Vérifie la signature via JWKS Apple et l'audience via APPLE_CLIENT_ID.
    """
    id_token = request.data.get('id_token')
    if not id_token:
        return Response({'detail': 'id_token requis.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        client = PyJWKClient('https://appleid.apple.com/auth/keys')
        signing_key = client.get_signing_key_from_jwt(id_token)
        audience = os.getenv('APPLE_CLIENT_ID')
        data = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience if audience else None,
            issuer='https://appleid.apple.com',
            options={"verify_aud": bool(audience)}
        )
        email = data.get('email')
        if not email:
            # Some flows only provide sub; create a pseudo email
            email = f"apple_{data.get('sub')}@apple.local"
        # Upsert user
        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            base_username = (email.split('@')[0])[:20] or 'user'
            candidate = base_username
            i = 1
            while Utilisateur.objects.filter(username=candidate).exists():
                candidate = f"{base_username}{i}"
                i += 1
            user = Utilisateur.objects.create_user(username=candidate, email=email)
        updates = []
        if not user.is_active:
            user.is_active = True; updates.append('is_active')
        if not getattr(user, 'est_verifie', False):
            user.est_verifie = True; updates.append('est_verifie')
        if updates:
            user.save(update_fields=updates)
        payload = {'utilisateur': UtilisateurSerializer(user).data}
        if HAS_JWT and RefreshToken is not None:
            refresh = RefreshToken.for_user(user)
            payload.update({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(payload)
    except Exception as e:
        return Response({'detail': f'Erreur Apple Sign-In: {e}'}, status=status.HTTP_400_BAD_REQUEST)

class ProfilViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des profils utilisateur"""
    
    queryset = ProfilUtilisateur.objects.select_related('utilisateur')
    serializer_class = ProfilUtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated, IsProprietaireProfil]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(utilisateur=self.request.user)
    
    @action(detail=True, methods=['post'])
    def ajouter_magasin_prefere(self, request, pk=None):
        """Ajouter un magasin aux préférés"""
        profil = self.get_object()
        magasin_id = request.data.get('magasin_id')
        
        if not magasin_id:
            return Response(
                {'error': _('ID du magasin requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profil.magasins_preferes.add(magasin_id)
        return Response({'message': _('Magasin ajouté aux préférés.')})
    
    @action(detail=True, methods=['post'])
    def ajouter_categorie_remise(self, request, pk=None):
        """Ajouter une catégorie aux préférences de remise"""
        profil = self.get_object()
        categorie_id = request.data.get('categorie_id')
        
        if not categorie_id:
            return Response(
                {'error': _('ID de la catégorie requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profil.categories_preferees_remises.add(categorie_id)
        return Response({'message': _('Catégorie ajoutée aux préférences.')})

class AbonnementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour la gestion des abonnements"""
    
    queryset = Abonnement.objects.select_related('utilisateur')
    serializer_class = AbonnementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(utilisateur=self.request.user)