# Generated manually to fix missing produit_id column
# Note: Cette migration est redondante car la migration 0012 a déjà ajouté le champ produit.
# Elle est conservée pour compatibilité mais ne fait rien car le champ existe déjà.
from django.db import migrations


def noop_forward(apps, schema_editor):
    """Fonction no-op : le champ produit a déjà été ajouté dans la migration 0012"""
    pass


def noop_reverse(apps, schema_editor):
    """Fonction no-op pour la migration inverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0012_homologationproduit_produit'),
    ]

    operations = [
        # Migration no-op : le champ produit a déjà été ajouté dans la migration 0012
        # Cette migration est conservée pour compatibilité mais ne fait rien
        migrations.RunPython(noop_forward, noop_reverse),
    ]

