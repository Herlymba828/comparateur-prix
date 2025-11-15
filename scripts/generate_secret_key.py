#!/usr/bin/env python
"""
Script pour générer une clé secrète Django sécurisée
Usage: python scripts/generate_secret_key.py
"""
from secrets import token_urlsafe

if __name__ == '__main__':
    secret_key = token_urlsafe(50)
    print("=" * 70)
    print("CLÉ SECRÈTE DJANGO GÉNÉRÉE")
    print("=" * 70)
    print()
    print("Copiez cette clé dans votre fichier .env :")
    print()
    print(f"DJANGO_SECRET_KEY={secret_key}")
    print()
    print("=" * 70)
    print("⚠️  IMPORTANT: Ne partagez JAMAIS cette clé publiquement!")
    print("=" * 70)

