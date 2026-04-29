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

**Impacts :** Présence de `pyproject.toml`, `uv.lock`, `.python-version`, `requirements.txt`. Commande de lancement : `uv run python -m src.migrate`. Dans le `Dockerfile.migrator`, on installe via `pip install -r requirements.txt` pour rester portable et léger côté image.

---

## 2026-04-28 — Version de Python : 3.13

**Contexte :** Python 3.14 récemment sorti, 3.13 stable et largement supporté, 3.12 LTS de fait.

**Options envisagées :** 3.12, 3.13, 3.14.

**Décision :** Python 3.13.

**Justification :** Compromis récence / stabilité de l'écosystème. Tous les paquets utilisés (pandas, pymongo, pytest) ont des wheels précompilés. 3.14 trop récent (risque de wheels manquants), 3.12 plus ancien.

**Alternatives écartées :** 3.14 (trop récent), 3.12 (un peu ancien, sans avantage).

**Impacts :** `.python-version` pointe sur 3.13. Répliqué dans le `Dockerfile.migrator` (`FROM python:3.13-slim`).

---

## 2026-04-28 — MongoDB local via conteneur Docker dès le début (image `mongo:8.2`)

**Contexte :** L'étape 1 demande « installer MongoDB en local ». Deux interprétations : installation native Windows ou conteneur. Il faut aussi choisir une version d'image.

**Options envisagées :** MongoDB Community natif Windows vs conteneur ; pour la version : `mongo:7`, `mongo:8.0`, `mongo:8.2`.

**Décision :** Conteneur `mongo:8.2` dès la phase d'exploration.

**Justification :** Le choix conteneur est dicté par : (1) alignement avec l'étape 2 qui exige Docker — pas de désinstallation à faire ensuite, (2) reproductibilité sur n'importe quelle machine, (3) pratique standard d'un Data Engineer aujourd'hui, (4) « en local » signifie « sur ma machine », ce que fait Docker Desktop. Pour la version : `mongo:7` initialement envisagé mais sa fin de support est annoncée pour août 2026, ce qui rendrait le projet obsolète avant la soutenance ; `mongo:8.2` est la version mineure stable la plus récente, cohérente avec une posture de Data Engineer veillant à utiliser des versions encore supportées.

**Alternatives écartées :** Installation native Windows (lourde, à désinstaller plus tard, non alignée avec la suite du projet) ; `mongo:7` (fin de support proche) ; `mongo:8.0` (LTS, plus conservateur, mais sans bénéfice ici).

**Impacts :** Tout le pipeline cible MongoDB 8.2. Le service `mongodb` du `docker-compose.yml` utilise l'image `mongo:8.2`. Compatibilité descendante du driver `pymongo` vérifiée (4.17+).

---

## 2026-04-28 — Pas d'authentification MongoDB en phase 1 (exploration)

**Contexte :** L'étape 1 ne mentionne pas l'authentification. L'authentification + rôles est une compétence évaluée traitée en étape 2 (conteneurisation).

**Options envisagées :** Auth dès l'exploration, auth uniquement à partir de Docker Compose.

**Décision :** Pas d'auth en phase 1. Auth introduite avec Docker Compose en étape 2.

**Justification :** Séparation des préoccupations. Lors du développement du pipeline de migration, l'objectif est de valider la logique métier (parsing, transformation, indexation). Mêler auth et logique métier dans la même itération multiplie les sources d'erreur. La compétence « système d'authentification » sera pleinement traitée et démontrée en étape 2 sur l'infrastructure cible (Docker Compose).

**Alternatives écartées :** Auth dès le début (ralentit l'itération sans bénéfice pédagogique sur cette phase).

**Impacts :** `MONGO_URI` par défaut sans credentials en phase 1. Surchargé via variable d'environnement quand l'auth est activée à l'étape 2.

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

**Impacts :** 54 966 documents en base au lieu de 55 500. Tests `test_count_matches_csv_minus_duplicates` et `test_no_strict_duplicates` valident.

---

## 2026-04-28 — Convention de nommage des champs : snake_case

**Contexte :** Le CSV utilise des noms avec espaces et casse Title (`Date of Admission`, `Blood Type`). Inutilisable directement comme champs MongoDB (espaces autorisés mais pénibles à requêter).

**Options envisagées :** snake_case (`date_of_admission`), camelCase (`dateOfAdmission`), brut avec espaces.

**Décision :** snake_case.

**Justification :** Standard Python (PEP 8), accès direct via `pymongo` (`doc["date_of_admission"]`). MongoDB ne contraint pas la convention, donc on choisit celle qui s'aligne avec le langage qui pilote le pipeline.

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

## 2026-04-28 — Connexion conteneur → hôte Mongo : `host.docker.internal` au lieu de `--network host`

**Contexte :** Lors des tests avec `mongoexport`/`mongodump` depuis un conteneur jetable, première tentative avec `--network host`. Connexion réussie mais 0 records exportés.

**Options envisagées :** `--network host`, `host.docker.internal`, mappage explicite via `--add-host`.

**Décision :** Utiliser le DNS spécial `host.docker.internal` fourni par Docker Desktop pour résoudre l'IP de l'hôte. Cross-platform (Windows + macOS, et Linux récent).

**Justification :** `--network host` est une fonctionnalité Linux. Sur Docker Desktop Windows/macOS, l'option est acceptée silencieusement mais n'a pas l'effet attendu — le conteneur ne partage pas réellement la pile réseau de l'hôte. Le `localhost` du conteneur reste sa propre boucle locale. `host.docker.internal` règle le problème de manière portable.

**Alternatives écartées :** `--network host` (non fonctionnel sur Docker Desktop), `--add-host` manuel (plus fragile).

**Impacts :** Non bloquant en production avec Docker Compose (étape 2) — les services partagent un réseau Docker interne et utilisent les noms de service (`mongodb` au lieu de `host.docker.internal`). Cette subtilité disparaît une fois en infrastructure cible.

---

## 2026-04-28 — Export vers JSON Lines + CSV via script Python

**Contexte :** La consigne demande explicitement « importer **et exporter** l'ensemble des données ». Deux formats demandés par l'utilisateur final pour servir les besoins variés (interopérabilité, lisibilité Excel, ré-import Mongo).

**Options envisagées :** (a) JSONL seul, (b) CSV seul, (c) les deux, (d) seulement la documentation des outils CLI Mongo.

**Décision :** (c) Script Python `src/export.py` produisant les deux formats, **en plus** de la documentation des outils CLI (`mongoexport`, `mongodump`, `mongoimport`).

**Justification :** Complémentaires. **JSONL** préserve les types Mongo via extended JSON (`bson.json_util`) — réversible avec `mongoimport`. **CSV** est universel (Excel, Pandas) avec dates en ISO 8601, mais perd les types. Le script applicatif est testable et intégrable au pipeline ; les outils CLI démontrent la maîtrise de l'écosystème Mongo standard. Utiliser `bson.json_util` plutôt que `json` standard évite les pertes de types lors de l'export.

**Alternatives écartées :** (a)/(b) couvrent un seul cas d'usage, (d) ne valide pas la compétence d'écriture du pipeline.

**Impacts :** `src/export.py` produit `exports/patients_export.jsonl` et `exports/patients_export.csv`. Tests dédiés (`tests/test_export.py`) valident comptage, format ISO des dates, conformité du header CSV. Streaming via `collection.find()` pour ne pas charger toute la collection en mémoire.

---

## 2026-04-28 — Démonstration CRUD isolée dans `src/crud.py`

**Contexte :** La consigne demande explicitement « Utiliser les commandes de base pour CRUD via un script Python ». Le pipeline de migration ne couvre que Create + Read.

**Options envisagées :** (a) intégrer CRUD dans le pipeline de migration, (b) script séparé avec auto-nettoyage, (c) ne pas démontrer.

**Décision :** Script séparé `src/crud.py` qui démontre les 4 opérations sur des documents préfixés `Demo` et qui s'auto-nettoie.

**Justification :** Séparation des responsabilités (le script de migration n'a pas vocation à muter ou supprimer). Idempotence garantie : `count_documents` avant et après doit être identique. Démontre la maîtrise des opérations sans polluer la collection métier.

**Alternatives écartées :** (a) couple deux responsabilités sans valeur ajoutée, (c) ne couvre pas la compétence demandée.

**Impacts :** `src/crud.py` est documentaire/pédagogique, exécutable à la demande. Référencé dans le README.

---

## 2026-04-28 — Tests automatisés via pytest

**Contexte :** L'étape 1 demande « automatiser le processus de test ». Deux frameworks usuels : `unittest` (stdlib) et `pytest`.

**Options envisagées :** unittest (stdlib), pytest.

**Décision :** pytest.

**Justification :** Syntaxe plus concise (`assert` natif), fixtures plus expressives (`@pytest.fixture` partage les ressources entre tests), meilleure sortie console, écosystème de plugins. Référencé dans la ressource Real Python liée à la consigne.

**Alternatives écartées :** unittest (plus verbeux, moins ergonomique pour des tests d'intégration).

**Impacts :** `pyproject.toml` ajoute pytest en groupe `dev`. `pytest.ini` configure les chemins. 25 tests répartis en 3 fichiers (CSV, Mongo, exports). Lancement : `uv run pytest`.

---

## 2026-04-28 — Authentification MongoDB activée + 3 rôles distincts (moindre privilège)

**Contexte :** L'étape 2 demande explicitement la mise en place d'un système d'authentification. C'est une compétence évaluée. Il faut décider du nombre de comptes, de leurs rôles, et du modèle de séparation.

**Options envisagées :** (a) un seul compte admin pour tout, (b) admin + un compte applicatif, (c) admin + plusieurs comptes applicatifs avec rôles différenciés.

**Décision :** 3 comptes avec rôles cloisonnés :
- `admin` (rôle `root` sur la base `admin`) — administration ponctuelle uniquement (création d'utilisateurs, opérations système)
- `migration_user` (rôle `readWrite` sur `healthcare_db`) — utilisé par le pipeline de migration et les exports
- `analyst_user` (rôle `read` sur `healthcare_db`) — utilisé par les analystes pour consulter les données

**Justification :** Application stricte du principe du moindre privilège, recommandation universelle en sécurité (OWASP, NIST). Si les credentials du pipeline de migration sont compromis, l'attaquant peut écrire mais pas administrer. Si les credentials de l'analyste sont compromis, l'attaquant ne peut que lire — l'intégrité reste protégée. Documenter 3 rôles permet aussi de démontrer la compétence sécurité plutôt que de cocher une case.

**Alternatives écartées :** (a) viole le moindre privilège, antipattern, (b) ne distingue pas écriture et lecture donc rate la moitié de la démonstration sécurité.

**Impacts :** Variables d'env `MONGO_ADMIN_*`, `MIGRATION_USER_PASSWORD`, `ANALYST_USER_PASSWORD` dans `.env`. Tests manuels (`docs/security_tests.md`) prouvent que `analyst_user` ne peut effectivement pas écrire. Le `MONGO_URI` du pipeline utilise `migration_user`.

---

## 2026-04-28 — Création des utilisateurs applicatifs via `init-users.js` (`/docker-entrypoint-initdb.d/`)

**Contexte :** Une fois `migration_user` et `analyst_user` définis, il faut décider comment les créer dans MongoDB. L'admin est créé automatiquement par l'image officielle via les variables `MONGO_INITDB_ROOT_USERNAME`/`PASSWORD`. Pour les autres, plusieurs approches existent.

**Options envisagées :** (a) script externe à exécuter manuellement après `up`, (b) job Docker dédié à la création, (c) montage d'un script JS dans `/docker-entrypoint-initdb.d/` lu automatiquement par l'image officielle au premier démarrage.

**Décision :** Option (c) — fichier `mongo-init/init-users.js` monté en read-only dans `/docker-entrypoint-initdb.d/` du conteneur Mongo.

**Justification :** Approche officielle documentée par MongoDB. L'image lit automatiquement tout `*.js` ou `*.sh` présent dans ce dossier au tout premier démarrage (volume `mongo_data` vide). Aucune action manuelle, aucun service supplémentaire. Mots de passe injectés via les variables d'env passées au conteneur Mongo.

**Alternatives écartées :** (a) sape l'idée même de reproductibilité Docker (action manuelle nécessaire après chaque init), (b) ajoute un service entier pour ce qui peut tenir dans 10 lignes de JS.

**Impacts :** `mongo-init/init-users.js` versionné dans le repo (sans mots de passe — ils sont lus depuis l'environnement à l'exécution via `process.env`). Si le volume `mongo_data` n'est pas vide, le script ne se rejoue pas — c'est volontaire (pas de réinitialisation accidentelle des comptes). En cas de réinitialisation voulue : `docker compose down -v` puis `up`.

---

## 2026-04-28 — Pattern « migrator one-shot » : conteneur batch qui s'arrête après exécution

**Contexte :** Le pipeline de migration est un job batch ponctuel, pas un service permanent. Il faut décider de son cycle de vie dans le `docker-compose.yml`.

**Options envisagées :** (a) service long-running qui boucle ou attend, (b) conteneur one-shot qui exécute le script et exit, (c) lancement manuel hors Compose.

**Décision :** (b) Conteneur one-shot, déclaré comme service `migrator` dans Compose, qui exécute `python -m src.migrate` puis exit avec code 0.

**Justification :** Le pipeline est par nature non-permanent (ETL ponctuel). Un conteneur one-shot est explicite sur cette nature : `docker compose ps` montre `migrator: Exited (0)` après succès, signal clair pour l'évaluateur ou un opérateur. Lancement reproductible via `docker compose up`. Pas de boucle d'attente, pas de redémarrage en cas de succès (option `restart: "no"`). Healthcheck Mongo + `depends_on` garantit que le pipeline ne démarre pas avant que la base soit prête.

**Alternatives écartées :** (a) gaspillage de ressources, ne reflète pas la nature du pipeline, (c) sape la reproductibilité Docker — l'évaluateur ne pourrait pas tout reproduire avec une seule commande.

**Impacts :** Service `migrator` dans `docker-compose.yml` avec `depends_on: mongodb (condition: service_healthy)`. Au démarrage de la stack : Mongo lance, devient healthy, migrator démarre, exécute, sort. Stack stable ensuite avec uniquement Mongo en service permanent.

---

## 2026-04-28 — Healthcheck MongoDB + dépendance ordonnée Compose

**Contexte :** Sans synchronisation, le `migrator` peut démarrer avant que Mongo n'ait fini son init (création utilisateurs, ouverture du port en mode auth). Résultat : erreurs de connexion ou d'auth sporadiques.

**Options envisagées :** (a) `depends_on` simple (attend juste que le conteneur démarre, pas qu'il soit prêt), (b) healthcheck custom + `depends_on` avec condition `service_healthy`, (c) script `wait-for-it.sh` côté migrator.

**Décision :** (b) — Healthcheck défini sur le service `mongodb` qui ping la base via `mongosh`, et `depends_on` avec `condition: service_healthy` côté migrator.

**Justification :** Approche déclarative, gérée nativement par Docker Compose. Pas de dépendance à un script externe. Le healthcheck vérifie le succès d'une commande ping, ce qui prouve que Mongo accepte les connexions ET que l'init est terminée. Compose attend vraiment que le service soit prêt avant de démarrer les dépendants.

**Alternatives écartées :** (a) ne synchronise rien d'utile (fonctionnellement équivalent à pas de `depends_on`), (c) ajoute une dépendance externe et un script à maintenir.

**Impacts :** Bloc `healthcheck` dans le service `mongodb` avec interval/timeout/retries calibrés. `depends_on` du `migrator` utilise `condition: service_healthy`. Premier démarrage légèrement plus long mais fiable.

---

## 2026-04-28 — Migrator dockerisé dès l'étape 2 (image dédiée)

**Contexte :** En phase 1, le pipeline tournait depuis l'hôte Windows en `uv run python -m src.migrate`, ciblant un Mongo conteneurisé. En étape 2, il faut décider si on garde ce mode hybride ou si on dockerise aussi le migrator.

**Options envisagées :** (a) garder le migrator hôte, (b) dockeriser le migrator en image dédiée, (c) image multi-services unique.

**Décision :** (b) — image dédiée `Dockerfile.migrator` basée sur `python:3.13-slim`, qui copie `src/` et installe les dépendances via `pip install -r requirements.txt`.

**Justification :** Pour la consigne, le livrable doit pouvoir tourner avec une seule commande (`docker compose up`). Le mode hybride imposait à l'évaluateur d'avoir Python + uv installés, contraire à l'esprit Docker. Dockerisation = reproductibilité totale, indépendante de l'OS de l'évaluateur. Image `slim`. Installation via `pip install -r requirements.txt` (pas `uv` dans le conteneur) pour un Dockerfile minimal — uv reste l'outil de dev, pip est suffisant pour l'image cible.

**Alternatives écartées :** (a) requiert outillage côté évaluateur, (c) couple les responsabilités MongoDB et migration dans une image, antipattern.

**Impacts :** Présence de `Dockerfile.migrator` à la racine, service `migrator` dans `docker-compose.yml`. `requirements.txt` (généré via `uv export`) devient le contrat de dépendances pour le build. Toute modif des dépendances suit le cycle : `uv add ...` → `uv export` → rebuild image.

---

## 2026-04-28 — Gestion des secrets via fichier `.env` non versionné + `.env.example`

**Contexte :** Les mots de passe MongoDB (admin, migration_user, analyst_user) ne doivent pas se retrouver dans le repo Git. Il faut un mécanisme de gestion de secrets simple, adapté au contexte pédagogique mais représentatif des bonnes pratiques.

**Options envisagées :** (a) hardcoder dans `docker-compose.yml`, (b) fichier `.env` non versionné + `.env.example` versionné, (c) Docker secrets, (d) gestionnaire externe (Vault, AWS Secrets Manager).

**Décision :** (b) — fichier `.env` à la racine, ignoré par Git via `.gitignore`, accompagné d'un `.env.example` versionné qui documente les variables attendues sans les valeurs.

**Justification :** Bon compromis simplicité/sécurité pour un projet de cette taille. `.env.example` permet à un nouveau contributeur (ou à l'évaluateur) de savoir quelles variables remplir, sans exposer les vraies valeurs. Lu nativement par Docker Compose. Lu en Python via `python-dotenv` (chargé dans `src/config.py` pour usage hors Docker, comme pytest local).

**Alternatives écartées :** (a) fuite immédiate dans Git, (c) Docker secrets sont surtout pertinents en mode swarm/production, sur-dimensionnés ici, (d) hors périmètre projet.

**Impacts :** `.gitignore` exclut `.env`. `.env.example` versionné avec placeholders. `python-dotenv` ajouté en dépendance dev. Bloc `try: from dotenv import load_dotenv; load_dotenv() except ImportError: pass` en tête de `src/config.py` pour rendre le chargement optionnel (Docker injecte les vars directement, pas besoin de python-dotenv côté conteneur). Doc d'installation du README explique la copie de `.env.example` vers `.env` et le remplissage par l'utilisateur.

---

## État actuel du projet

À la fin de l'étape 2 (28/04/2026), toutes les décisions structurantes du périmètre Docker / MongoDB / pipeline sont tracées. Les décisions à venir relèvent de l'étape 3 (recherches AWS) et seront documentées au moment où elles seront prises (choix DocumentDB vs RDS, modèle de tarification retenu, etc.).