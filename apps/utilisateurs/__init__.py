default_app_config = 'apps.utilisateurs.apps.UtilisateursConfig'
"""
Les signaux sont importés dans UtilisateursConfig.ready().
Ne pas importer les signaux ici pour éviter AppRegistryNotReady lors du chargement des apps.
"""