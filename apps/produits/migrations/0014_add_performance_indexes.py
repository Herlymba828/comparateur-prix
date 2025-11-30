# Generated migration for performance indexes

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0013_add_produit_column_manual'),
    ]

    operations = [
        # Index sur nom pour recherches (avec fonction LOWER pour recherches case-insensitive)
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_produit_nom_icontains 
                ON produits_produit (LOWER(nom));
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_produit_nom_icontains;"
        ),
        # Index composite pour prix (produit_id, est_disponible, prix_actuel)
        # Améliore les requêtes de recherche de prix minimum/maximum
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_prix_produit_disponible 
                ON produits_prix (produit_id, est_disponible, prix_actuel)
                WHERE est_disponible = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_prix_produit_disponible;"
        ),
        # Index sur date_modification pour filtres temporels
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_prix_date_modification 
                ON produits_prix (date_modification);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_prix_date_modification;"
        ),
        # Index sur est_actif pour filtrer rapidement les produits actifs
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_produit_est_actif 
                ON produits_produit (est_actif)
                WHERE est_actif = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_produit_est_actif;"
        ),
        # Index composite pour catégorie et marque (utilisé dans les filtres)
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS idx_produit_categorie_marque 
                ON produits_produit (categorie_id, marque_id)
                WHERE est_actif = true;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_produit_categorie_marque;"
        ),
    ]

