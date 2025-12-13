"""
Middleware de compression avancé pour optimiser la taille des réponses.
"""
import gzip
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
import io


class SmartCompressionMiddleware(MiddlewareMixin):
    """
    Middleware de compression intelligent qui compresse les réponses JSON.
    Plus efficace que GZipMiddleware standard.
    """
    
    # Taille minimale pour la compression (en bytes)
    MIN_SIZE = 200
    
    # Types de contenu à compresser
    COMPRESSIBLE_TYPES = (
        'application/json',
        'application/javascript',
        'text/html',
        'text/css',
        'text/plain',
        'text/xml',
        'application/xml',
    )
    
    def process_response(self, request, response):
        """Compresser la réponse si nécessaire."""
        
        # Ne pas compresser si déjà compressé
        if response.get('Content-Encoding') == 'gzip':
            return response
        
        # Ne pas compresser les petites réponses
        if not response.streaming and len(response.content) < self.MIN_SIZE:
            return response
        
        # Vérifier si le client accepte gzip
        ae = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if 'gzip' not in ae.lower():
            return response
        
        # Vérifier le type de contenu
        content_type = response.get('Content-Type', '').split(';')[0].strip()
        if content_type not in self.COMPRESSIBLE_TYPES:
            return response
        
        # Compresser le contenu
        if response.streaming:
            # Pour les réponses streaming, ne pas compresser
            return response
        
        try:
            # Compresser avec gzip
            compressed_content = self._compress(response.content)
            
            # Vérifier que la compression est bénéfique
            if len(compressed_content) < len(response.content):
                response.content = compressed_content
                response['Content-Encoding'] = 'gzip'
                response['Content-Length'] = str(len(compressed_content))
                
                # Ajouter un header pour indiquer le taux de compression
                original_size = len(response.content)
                compression_ratio = (1 - len(compressed_content) / original_size) * 100
                response['X-Compression-Ratio'] = f"{compression_ratio:.1f}%"
        
        except Exception:
            # En cas d'erreur, retourner la réponse non compressée
            pass
        
        return response
    
    def _compress(self, content):
        """Compresser le contenu avec gzip."""
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as f:
            f.write(content)
        return buf.getvalue()


class JSONMinificationMiddleware(MiddlewareMixin):
    """
    Middleware pour minifier les réponses JSON.
    Supprime les espaces inutiles pour réduire la taille.
    """
    
    def process_response(self, request, response):
        """Minifier les réponses JSON."""
        
        # Vérifier si c'est du JSON
        content_type = response.get('Content-Type', '').split(';')[0].strip()
        if content_type != 'application/json':
            return response
        
        # Ne pas minifier si déjà petit
        if len(response.content) < 100:
            return response
        
        try:
            # Parser et re-sérialiser sans espaces
            data = json.loads(response.content)
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            
            # Calculer la réduction
            original_size = len(response.content)
            minified_size = len(minified.encode('utf-8'))
            
            if minified_size < original_size:
                response.content = minified.encode('utf-8')
                response['Content-Length'] = str(minified_size)
                
                # Ajouter un header pour indiquer la réduction
                reduction = (1 - minified_size / original_size) * 100
                response['X-JSON-Minification'] = f"{reduction:.1f}%"
        
        except (json.JSONDecodeError, UnicodeDecodeError):
            # En cas d'erreur, retourner la réponse originale
            pass
        
        return response
