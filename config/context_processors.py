from django.conf import settings

def social_providers(request):
    """Expose which social providers are enabled to templates."""
    google_enabled = bool(getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) and getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', None))
    facebook_enabled = bool(getattr(settings, 'SOCIAL_AUTH_FACEBOOK_KEY', None) and getattr(settings, 'SOCIAL_AUTH_FACEBOOK_SECRET', None))
    apple_enabled = bool(getattr(settings, 'ENABLE_APPLE_AUTH', False))
    return {
        'social_google_enabled': google_enabled,
        'social_facebook_enabled': facebook_enabled,
        'social_apple_enabled': apple_enabled,
    }


def public_settings(request):
    """Expose selected safe settings to templates."""
    return {
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    }
