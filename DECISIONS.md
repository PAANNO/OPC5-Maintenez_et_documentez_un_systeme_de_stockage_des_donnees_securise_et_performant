# Journal des décisions techniques — OPC5

Ce fichier trace les choix structurants du projet. Il sert de support en soutenance.
Format inspiré des ADR (Architecture Decision Records).

---

## 2026-04-28 — Choix de MongoDB comme moteur NoSQL

**Contexte :** La consigne impose MongoDB nommément. Aucune marge de choix sur la techno principale, mais il faut être capable de justifier le choix face à un évaluateur jouant le client.

**Options envisagées :** MongoDB (imposé), Cassandra, Redis, Elasticsearch.

**Décision :** MongoDB.

**Justification :** Imposé par la consigne. Au-delà de l'imposition, MongoDB est pertinent pour ce dataset car : (1) données documentaires hétérogènes par patient, (2) requêtes ad hoc fréquentes côté client (famille « document store »), (3) scalabilité horizontale par sharding native, (4) compatibilité directe avec Amazon DocumentDB pour l'évolution cloud.

**Alternatives écartées :** Cassandra (orienté colonne, moins adapté aux requêtes ad hoc), Redis (clé-valeur, persistance secondaire), Elasticsearch (orienté recherche, pas BDD principale).

**Impacts :** Conditionne tout le pipeline (driver `pymongo`), le format des tests, et la trajectoire AWS (DocumentDB privilégié à RDS).

---

## 2026-04-28 — Conteneurisation via Docker Compose plutôt que Docker seul

**Contexte :** Le projet implique au minimum 2 services (MongoDB + script de migration). Il faut orchestrer leur démarrage et leurs dépendances.

**Options envisagées :** Docker run manuels, Docker Compose, Kubernetes/Minikube.

**Décision :** Docker Compose.

**Justification :** Imposé par la consigne (livrable n°3). Adapté à la complexité du projet : permet de définir réseau, volumes, dépendances `depends_on`, variables d'environnement dans un seul fichier reproductible.

**Alternatives écartées :** `docker run` manuels (non reproductible, hors consigne) ; Kubernetes (sur-dimensionné).

**Impacts :** Le livrable n°3 est `docker-compose.yml`. Toute la doc d'installation tourne autour de `docker compose up`.

---

## 2026-04-28 — Gestionnaire d'environnement Python : uv

**Contexte :** Le projet nécessite un environnement Python isolé et reproductible. Plusieurs options existent (venv + pip, conda, poetry, uv).

**Options envisagées :** venv + pip + requirements.txt, Poetry, uv.

**Décision :** uv (avec génération d'un `requirements.txt` en parallèle pour la consigne).

**Justification :** uv est le gestionnaire de référence Python moderne (Astral, 2024+) : ultra-rapide (résolution en ms vs s pour pip), gère versions Python + venv + dépendances dans un seul outil, lockfile déterministe (`uv.lock`). OpenClassrooms propose même un cours dédié dans le parcours. Le `requirements.txt` reste exigé par la consigne et est généré automatiquement via `uv export`.

**Alternatives écartées :** Poetry (plus lent, moins moderne), pip + venv pur (gestion manuelle de la version Python, lockfile non-officiel).

**Impacts :** Présence de `pyproject.toml`, `uv.lock`, `.python-version`, `requirements.txt`. Commande de lancement : `uv run python -m src.migrate`. Dans le `Dockerfile.migrator` (à venir), on installera via `pip install -r requirements.txt` pour rester portable et léger.

---

## 2026-04-28 — Version de Python : 3.13

**Contexte :** Python 3.14 récemment sorti, 3.13 stable et largement supporté, 3.12 LTS de fait.

**Options envisagées :** 3.12, 3.13, 3.14.

**Décision :** Python 3.13.

**Justification :** Compromis récence / stabilité de l'écosystème. Tous les paquets utilisés (pandas, pymongo, pytest) ont des wheels précompilés. 3.14 trop récent (risque de wheels manquants), 3.12 plus ancien.

**Alternatives écartées :** 3.14 (trop récent), 3.12 (un peu ancien, sans avantage).

**Impacts :** `.python-version` pointe sur 3.13. À répliquer dans le `Dockerfile.migrator` (`FROM python:3.13-slim`).

---

## 2026-04-28 — MongoDB local via conteneur Docker dès le début

**Contexte :** L'étape 1 demande « installer MongoDB en local ». Deux interprétations : installation native Windows ou conteneur.

**Options envisagées :** MongoDB Community natif Windows, conteneur `mongo:7`.

**Décision :** Conteneur `mongo:7` dès la phase d'exploration.

**Justification :** (1) Aligne avec l'étape 2 qui exige Docker — pas de désinstallation à faire. (2) Reproductible sur n'importe quelle machine. (3) Pratique standard d'un Data Engineer aujourd'hui. (4) « En local » signifie « sur ma machine », ce que fait Docker Desktop.

**Alternatives écartées :** Installation native Windows (lourde, à désinstaller plus tard, non aligned avec la suite du projet).

**Impacts :** Commande `docker run` documentée pour la phase d'exploration. La phase 2 remplacera ce conteneur isolé par un service du `docker-compose.yml`.

---

## 2026-04-28 — Pas d'authentification MongoDB en phase 1 (exploration)

**Contexte :** L'étape 1 ne mentionne pas l'authentification. L'authentification + rôles est une compétence évaluée traitée en étape 2 (conteneurisation).

**Options envisagées :** Auth dès l'exploration, auth uniquement à partir de Docker Compose.

**Décision :** Pas d'auth en phase 1. Auth introduite avec Docker Compose en étape 2.

**Justification :** Séparation des préoccupations. Lors du développement du pipeline de migration, l'objectif est de valider la logique métier (parsing, transformation, indexation). Mêler auth et logique métier dans la même itération multiplie les sources d'erreur. La compétence « système d'authentification » sera pleinement traitée et démontrée en étape 2 sur l'infrastructure cible (Docker Compose).

**Alternatives écartées :** Auth dès le début (ralentit l'itération sans bénéfice pédagogique sur cette phase).

**Impacts :** `MONGO_URI` par défaut sans credentials en phase 1. À surcharger via variable d'environnement quand auth sera activée.

---

## 2026-04-28 — Casse des champs nominatifs : Title Case à la migration

**Contexte :** Le dataset Kaggle contient des noms en casse aléatoire (`Bobby JacksOn`, `LesLie TErRy`, `andrEw waTtS`...). 49 992 valeurs uniques sur 55 500 lignes pour `Name`.

**Options envisagées :** (a) Normaliser en Title Case à la migration, (b) garder le brut + ajouter un champ `name_normalized` indexable, (c) garder brut sans rien faire.

**Décision :** Normaliser en Title Case sur `name` et `doctor` à la migration via `.str.strip().str.title()`.

**Justification :** Lisibilité des données en sortie, simplicité d'implémentation, suffisant pour les besoins du projet pédagogique. La logique « brut + normalisé » est plus pro mais ajoute de la complexité non exploitée ici.

**Alternatives écartées :** (b) ajoute un champ supplémentaire sans bénéfice mesurable, (c) laisse des données inexploitables.

**Impacts :** Transformation déterministe dans `transform()`. Test `test_names_are_title_case` valide la normalisation post-migration.

---

## 2026-04-28 — Doublons stricts : suppression à la migration

**Contexte :** Détection de 534 doublons stricts sur 55 500 lignes (~1 %). Les valeurs identiques sur 15 colonnes incluant un montant au centime près sont quasi certainement des artefacts.

**Options envisagées :** (a) supprimer pendant la migration, (b) conserver, (c) loguer mais conserver.

**Décision :** Suppression via `df.drop_duplicates()` pendant la phase de transformation.

**Justification :** Probabilité quasi nulle que 534 patients aient exactement le même nom, âge, médecin, hôpital, dates, montant facturé. Les conserver pollue les agrégations (avg, count) sans valeur ajoutée. Le nombre exact supprimé est logué pour traçabilité.

**Alternatives écartées :** (b) pollue les analyses, (c) ajoute du bruit sans action.

**Impacts :** 54 966 documents en base au lieu de 55 500. Test `test_count_matches_csv_minus_duplicates` valide. Test `test_no_strict_duplicates` garantit qu'aucun doublon ne subsiste.

---

## 2026-04-28 — Convention de nommage des champs : snake_case

**Contexte :** Le CSV utilise des noms avec espaces et casse Title (`Date of Admission`, `Blood Type`). Inutilisable directement comme champs MongoDB (espaces autorisés mais pénibles à requêter).

**Options envisagées :** snake_case (`date_of_admission`), camelCase (`dateOfAdmission`), brut avec espaces.

**Décision :** snake_case.

**Justification :** Standard Python (PEP 8), accès direct via `pymongo` (`doc["date_of_admission"]`). MongoDB ne contrainte pas la convention, donc on choisit celle qui s'aligne avec le langage qui pilote le pipeline.

**Alternatives écartées :** camelCase (idiomatique côté JS/Mongo shell, mais on pilote en Python), brut (espaces nécessitent du quoting partout).

**Impacts :** `RENAME_MAP` dans `src/config.py` mappe les colonnes CSV vers les noms snake_case.

---

## 2026-04-28 — Stratégie d'indexation : 3 simples + 1 composé

**Contexte :** Point de vigilance explicite de l'étape 1. Index nécessaires pour les requêtes attendues d'un système de gestion patients.

**Options envisagées :** (a) 4 index ciblés sur les cas d'usage métier, (b) index simples uniquement, (c) tout indexer.

**Décision :** 4 index :
- `idx_medical_condition` (simple, ascendant) — filtre par pathologie (cardinalité 6)
- `idx_date_of_admission_desc` (simple, descendant) — récupération admissions récentes
- `idx_hospital` (simple, ascendant) — filtre par établissement (cardinalité 39 876)
- `idx_age_gender` (composé) — analyses démographiques

**Justification :** Couvre les cas d'usage probables d'une application médicale : recherche par pathologie, dashboards récents, vues par hôpital, statistiques démographiques. Pas d'index sur `name` (cardinalité énorme, peu utile, coût en écriture). Pas d'index sur `billing_amount` (50 000 valeurs uniques, plus utile en agrégation).

**Alternatives écartées :** (b) trop pauvre pour démontrer la compétence, (c) coût de maintenance disproportionné, anti-pattern.

**Impacts :** Création via `IndexModel` après l'insertion (ordre optimal : insertion en bulk puis indexation, sinon ralentissement). Test `test_query_uses_index` vérifie via `explain()` que MongoDB utilise bien `IXSCAN` pour `medical_condition`.

---

## 2026-04-28 — Idempotence du script de migration

**Contexte :** Le script peut être lancé plusieurs fois (debug, mise à jour du dataset). Sans protection, chaque lancement ajouterait 54 966 documents en doublon.

**Options envisagées :** (a) `delete_many({})` avant insertion, (b) gestion d'`upsert` document par document, (c) accepter la non-idempotence.

**Décision :** `collection.delete_many({})` avant insertion.

**Justification :** Comportement déterministe : N exécutions → même état final. Simple à comprendre et à expliquer. L'`upsert` impliquerait une clé fonctionnelle stable (que `_id` ObjectId généré ne fournit pas), ajout de complexité non justifié pour un job de migration initiale.

**Alternatives écartées :** (b) overkill pour le cas d'usage, (c) source de bugs en debug.

**Impacts :** Méthode `load()` vide la collection avant `insert_many`. Documenté dans le README.

---

## 2026-04-28 — Connexion conteneur → hôte Mongo : host.docker.internal au lieu de --network host
**Contexte :** Lors des tests avec mongoexport/mongodump depuis un conteneur jetable, première tentative avec --network host. Connexion réussie mais 0 records exportés.

**Cause :** --network host est une fonctionnalité Linux. Sur Docker Desktop Windows/macOS, l'option est acceptée silencieusement mais n'a pas l'effet attendu — le conteneur ne partage pas réellement la pile réseau de l'hôte. Le localhost du conteneur reste sa propre boucle locale.

**Décision :** utiliser le DNS spécial host.docker.internal fourni par Docker Desktop pour résoudre l'IP de l'hôte. Cross-platform (Windows + macOS, et linux récent).

**Impact pour la suite :** non bloquant — en production avec Docker Compose (étape 2), tous les services partageront un réseau Docker interne et on utilisera les noms de service (mongodb au lieu de host.docker.internal). Cette subtilité disparaît une fois en infrastructure cible.

---

## 2026-04-28 — Pas d'authentification MongoDB en phase 1 (exploration et migration locale)

**Contexte :** L'étape 1 ne mentionne pas l'authentification. L'authentification + rôles est une compétence évaluée traitée en étape 2 (conteneurisation).

**Décision :** Pas d'auth en phase 1. Auth introduite avec Docker Compose en étape 2.

**Justification :** Séparation des préoccupations. Mêler auth et logique métier dans la même itération multiplie les sources d'erreur. La compétence « système d'authentification » sera pleinement traitée et démontrée en étape 2 sur l'infrastructure cible (Docker Compose).

**Impacts :** `MONGO_URI` par défaut sans credentials en phase 1. À surcharger via variable d'environnement quand l'auth sera activée.

---

## 2026-04-28 — Casse des champs nominatifs : Title Case à la migration

**Contexte :** Le dataset Kaggle contient des noms en casse aléatoire (`Bobby JacksOn`, `LesLie TErRy`...). 49 992 valeurs uniques sur 55 500 lignes pour `Name`.

**Options envisagées :** (a) normaliser en Title Case à la migration, (b) garder le brut + ajouter un champ `name_normalized` indexable, (c) garder brut.

**Décision :** Normaliser en Title Case sur `name` et `doctor` à la migration via `.str.strip().str.title()`.

**Justification :** Lisibilité, simplicité, suffisant pour les besoins du projet pédagogique. La logique « brut + normalisé » ajoute de la complexité non exploitée ici.

**Impacts :** Test `test_names_are_title_case` valide la normalisation post-migration.

---

## 2026-04-28 — Doublons stricts : suppression à la migration

**Contexte :** Détection de 534 doublons stricts sur 55 500 lignes (~1 %). Les valeurs identiques sur 15 colonnes incluant un montant au centime près sont quasi certainement des artefacts.

**Décision :** Suppression via `df.drop_duplicates()` pendant la phase de transformation.

**Justification :** Probabilité quasi nulle que 534 patients aient exactement le même nom, âge, médecin, hôpital, dates et montant. Les conserver pollue les agrégations (avg, count) sans valeur ajoutée. Le nombre supprimé est logué pour traçabilité.

**Impacts :** 54 966 documents en base. Tests `test_count_matches_csv_minus_duplicates` et `test_no_strict_duplicates` valident.

---

## 2026-04-28 — Convention de nommage des champs : snake_case

**Contexte :** Le CSV utilise des noms avec espaces et casse Title (`Date of Admission`, `Blood Type`). Inutilisable directement en MongoDB.

**Options envisagées :** snake_case, camelCase, brut avec espaces.

**Décision :** snake_case.

**Justification :** Standard Python (PEP 8). Accès direct via `pymongo` (`doc["date_of_admission"]`). MongoDB ne contraint pas la convention, on choisit celle qui s'aligne avec le langage qui pilote le pipeline.

**Impacts :** `RENAME_MAP` dans `src/config.py` mappe les colonnes CSV vers les noms snake_case.

---

## 2026-04-28 — Stratégie d'indexation : 3 simples + 1 composé

**Contexte :** Point de vigilance explicite de l'étape 1.

**Décision :** 4 index :
- `idx_medical_condition` (ascendant) — filtre par pathologie (cardinalité 6)
- `idx_date_of_admission_desc` (descendant) — récupération admissions récentes
- `idx_hospital` (ascendant) — filtre par établissement (cardinalité 39 876)
- `idx_age_gender` (composé) — analyses démographiques

**Justification :** Couvre les cas d'usage probables d'une application médicale : recherche par pathologie, dashboards récents, vues par hôpital, statistiques démographiques. Pas d'index sur `name` (cardinalité énorme, peu utile, coût en écriture). Pas d'index sur `billing_amount` (50 000 valeurs uniques, plus utile en agrégation qu'en filtre).

**Impacts :** Création via `IndexModel` après l'insertion (ordre optimal : insertion en bulk puis indexation, sinon ralentissement). Test `test_query_uses_index` vérifie via `explain()` que MongoDB utilise bien `IXSCAN`.

---

## 2026-04-28 — Idempotence du script de migration

**Contexte :** Le script peut être lancé plusieurs fois (debug, mise à jour du dataset). Sans protection, chaque lancement ajouterait 54 966 documents.

**Décision :** `collection.delete_many({})` avant insertion.

**Justification :** Comportement déterministe (N exécutions → même état final). Simple à expliquer. L'`upsert` impliquerait une clé fonctionnelle stable que `_id` ObjectId généré ne fournit pas.

**Impacts :** Méthode `load()` vide la collection avant `insert_many`. Documenté dans le README.

---

## 2026-04-28 — Export vers JSON Lines + CSV via script Python

**Contexte :** La consigne demande explicitement « importer **et exporter** l'ensemble des données ». Deux formats demandés par l'utilisateur final pour servir les besoins variés (interopérabilité, lisibilité Excel, ré-import Mongo).

**Options envisagées :** (a) JSONL seul, (b) CSV seul, (c) les deux, (d) seulement la documentation des outils CLI Mongo.

**Décision :** (c) Script Python `src/export.py` produisant les deux formats, **en plus** de la documentation des outils CLI (`mongoexport`, `mongodump`, `mongoimport`).

**Justification :** Complémentaires. **JSONL** préserve les types Mongo via extended JSON (`bson.json_util`) — réversible avec `mongoimport`. **CSV** est universel (Excel, Pandas) avec dates en ISO 8601, mais perd les types. Le script applicatif est testable et intégrable au pipeline ; les outils CLI démontrent la maîtrise de l'écosystème Mongo standard. Utiliser `bson.json_util` plutôt que `json` standard évite les pertes de types lors de l'export.

**Impacts :** `src/export.py` produit `exports/patients_export.jsonl` et `exports/patients_export.csv`. Tests dédiés (`tests/test_export.py`) valident comptage, format ISO des dates, conformité du header CSV. Streaming via `collection.find()` pour ne pas charger toute la collection en mémoire.

---

## 2026-04-28 — Démonstration CRUD isolée dans `src/crud.py`

**Contexte :** La consigne demande explicitement « Utiliser les commandes de base pour CRUD via un script python ». Le pipeline de migration ne couvre que Create + Read.

**Décision :** Script séparé `src/crud.py` qui démontre les 4 opérations sur des documents préfixés `Demo` et qui s'auto-nettoie.

**Justification :** Séparation des responsabilités (le script de migration n'a pas vocation à muter ou supprimer). Idempotence garantie : `count_documents` avant et après doit être identique. Démontre la maîtrise des opérations sans polluer la collection métier.

**Impacts :** `src/crud.py` est documentaire/pédagogique, exécutable à la demande. Référencé dans le README.

---

## 2026-04-28 — Tests automatisés via pytest

**Contexte :** L'étape 1 demande « automatiser le processus de test ». Deux frameworks usuels : `unittest` (stdlib) et `pytest`.

**Décision :** pytest.

**Justification :** Syntaxe plus concise (`assert` natif), fixtures plus expressives (`@pytest.fixture` partage les ressources entre tests), meilleure sortie console, écosystème de plugins. Référencé dans la ressource Real Python liée à la consigne.

**Impacts :** `pyproject.toml` ajoute pytest en groupe `dev`. `pytest.ini` configure les chemins. 25 tests répartis en 3 fichiers (CSV, Mongo, exports). Lancement : `uv run pytest`.

---

## [À compléter prochainement]

- Stratégie d'export (cf. décision en cours)
- Choix Dockerfile (image base, multistage ou pas)
- Stratégie auth + rôles MongoDB
- Stratégie volumes Docker
- Stratégie de gestion des secrets (.env)