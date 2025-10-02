from django.db import migrations, connections


def normalize_text(s: str) -> str:
    import unicodedata, re
    if not s:
        return ""
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s.strip()).lower()
    return s


def normalize_format(s: str) -> str:
    import re
    if not s:
        return ""
    s = s.strip().lower().replace(',', '.')
    s = normalize_text(s)
    s = re.sub(r"\s*x\s*", "x", s)
    s = s.replace(' kilogrammes', 'kg').replace(' litres', 'l')
    s = s.replace(' kilogramme', 'kg').replace(' litre', 'l')
    s = s.replace(' millilitres', 'ml').replace(' millilitre', 'ml')
    s = s.replace(' grammes', 'g').replace(' gramme', 'g')
    s = re.sub(r"\s+(kg|g|l|ml|cl)\b", r"\1", s)
    return s


def forwards(apps, schema_editor):
    # Add columns (safe if they don't exist). Using generic SQL for SQLite/Postgres.
    conn = schema_editor.connection
    # Vérifier l'existence des tables cibles; si absentes, sortir sans erreur
    try:
        existing_tables = set(conn.introspection.table_names())
    except Exception:
        existing_tables = set()

    has_homologation = 'produits_homologationproduit' in existing_tables
    has_prixhomologue = 'produits_prixhomologue' in existing_tables

    if not has_homologation and not has_prixhomologue:
        # Rien à faire pour cette base/ordre de migrations
        return
    if has_homologation:
        with conn.cursor() as cursor:
            # Add columns to produits_homologationproduit
            try:
                cursor.execute("""
                    ALTER TABLE produits_homologationproduit ADD COLUMN nom_norm VARCHAR(255) NOT NULL DEFAULT ''
                """)
            except Exception:
                pass
            try:
                cursor.execute("""
                    ALTER TABLE produits_homologationproduit ADD COLUMN marque_norm VARCHAR(120) NOT NULL DEFAULT ''
                """)
            except Exception:
                pass
            try:
                cursor.execute("""
                    ALTER TABLE produits_homologationproduit ADD COLUMN format_norm VARCHAR(120) NOT NULL DEFAULT ''
                """)
            except Exception:
                pass

    # Data migration: fill *_norm
    if has_homologation:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, nom, marque, format FROM produits_homologationproduit")
            rows = cursor.fetchall()
            for rid, nom, marque, fmt in rows:
                nom_n = normalize_text(nom or '')
                marque_n = normalize_text(marque or '')
                format_n = normalize_format(fmt or '')
                cursor.execute(
                    "UPDATE produits_homologationproduit SET nom_norm=%s, marque_norm=%s, format_norm=%s WHERE id=%s",
                    [nom_n[:255], marque_n[:120], format_n[:120], rid]
                )

    # Indexes and unique constraint
    with conn.cursor() as cursor:
        # Indexes on homologation
        if has_homologation:
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_nom_norm_cat ON produits_homologationproduit (nom_norm, categorie)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_marque_norm ON produits_homologationproduit (marque_norm)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ph_format_norm ON produits_homologationproduit (format_norm)")
            except Exception:
                pass
            # Unique constraint
            try:
                cursor.execute("""
                    ALTER TABLE produits_homologationproduit
                    ADD CONSTRAINT uq_ph_norm UNIQUE (nom_norm, marque_norm, format_norm, categorie)
                """)
            except Exception:
                # ignore if already exists or DB doesn't support direct statement
                pass
        # Indexes on produits_prixhomologue
        if has_prixhomologue:
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pp_produit ON produits_prixhomologue (produit_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pp_date_pub ON produits_prixhomologue (date_publication DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pp_localisation ON produits_prixhomologue (localisation)")
            except Exception:
                pass


def backwards(apps, schema_editor):
    # Non-destructive rollback: keep columns and indexes.
    # Optionally, drop indexes/constraint if needed.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("produits", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
