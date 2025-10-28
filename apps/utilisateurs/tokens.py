from typing import Any, Dict
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers

User = get_user_model()

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Remplacer username par email côté payload d'entrée
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    # Supprimer 'username' du champ requis hérité
    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        email = attrs.get('email')
        password = attrs.get('password')
        if not email or not password:
            raise serializers.ValidationError({'detail': 'email et password requis.'})
        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # mimer la réponse SimpleJWT standard
            raise serializers.ValidationError({'detail': 'No active account found with the given credentials'})
        # Mapper vers le schéma attendu par TokenObtainPairSerializer (username + password)
        attrs = {'username': getattr(user_obj, User.USERNAME_FIELD, user_obj.username), 'password': password}
        return super().validate(attrs)

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
