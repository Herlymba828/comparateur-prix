#!/usr/bin/env python
"""Script rapide pour ajouter des prix d'exemple"""
import os, sys, django
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
import random

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.produits.models import Produit, Prix
from apps.magasins.models import Magasin

print('Ajout de prix d exemple...')

produits = list(Produit.objects.all()[:10])  # 10 premiers produits
magasins = list(Magasin.objects.all()[:15])  # 15 premiers magasins

prix_count = 0
for produit in produits:
    prix_base = Decimal(random.uniform(2.0, 15.0))
    
    for magasin in random.sample(magasins, min(len(magasins), 8)):
        variation = Decimal(random.uniform(0.9, 1.1))
        prix_actuel = (prix_base * variation).quantize(Decimal('0.01'))
        
        prix, created = Prix.objects.get_or_create(
            produit=produit,
            magasin=magasin,
            defaults={
                'prix_actuel': prix_actuel,
                'est_disponible': True,
            }
        )
        if created:
            prix_count += 1

print(f'{prix_count} prix crees')
print(f'Total: {Prix.objects.count()} prix')
