# Generated manually to fix missing produit_id column
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0012_homologationproduit_produit'),
    ]

    operations = [
        # Vérifier et ajouter la colonne si elle n'existe pas
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='produits_homologationproduit' 
                        AND column_name='produit_id'
                    ) THEN
                        ALTER TABLE produits_homologationproduit 
                        ADD COLUMN produit_id BIGINT NULL;
                        ALTER TABLE produits_homologationproduit 
                        ADD CONSTRAINT produits_homologationproduit_produit_id_fk 
                        FOREIGN KEY (produit_id) REFERENCES produits_produit(id) 
                        ON DELETE SET NULL;
                        CREATE UNIQUE INDEX IF NOT EXISTS produits_homologationproduit_produit_id_key 
                        ON produits_homologationproduit(produit_id) WHERE produit_id IS NOT NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE produits_homologationproduit 
                DROP COLUMN IF EXISTS produit_id;
            """
        ),
    ]

