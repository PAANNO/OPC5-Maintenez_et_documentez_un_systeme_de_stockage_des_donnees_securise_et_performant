# OPC5 — Maintenez et documentez un système de stockage des données sécurisé et performant

> Projet 5 de la formation **Data Engineer OpenClassrooms** — Migration d'un dataset médical CSV vers MongoDB, conteneurisé via Docker, avec authentification, rôles utilisateurs, tests automatisés et exploration des options AWS.

---

## 📋 Sommaire

- [OPC5 — Maintenez et documentez un système de stockage des données sécurisé et performant](#opc5--maintenez-et-documentez-un-système-de-stockage-des-données-sécurisé-et-performant)
  - [📋 Sommaire](#-sommaire)
  - [1. Contexte et objectifs](#1-contexte-et-objectifs)
  - [2. Architecture](#2-architecture)
  - [3. Schéma de la base de données](#3-schéma-de-la-base-de-données)
  - [4. Sécurité — authentification et rôles](#4-sécurité--authentification-et-rôles)
  - [5. Prérequis](#5-prérequis)
  - [6. Installation et lancement](#6-installation-et-lancement)
  - [7. Logique de la migration](#7-logique-de-la-migration)
    - [Démonstration CRUD](#démonstration-crud)
    - [Export](#export)
  - [8. Tests](#8-tests)
  - [8. Tests](#8-tests-1)
  - [9. Structure du dépôt](#9-structure-du-dépôt)
  - [10. Recherches AWS](#10-recherches-aws)
  - [11. Décisions techniques](#11-décisions-techniques)
  - [12. Matrice consigne / livrables / preuves](#12-matrice-consigne--livrables--preuves)
  - [13. État d'avancement](#13-état-davancement)
  - [14. Limites connues](#14-limites-connues)
  - [15. Auteur et contexte de formation](#15-auteur-et-contexte-de-formation)

---

## 1. Contexte et objectifs

**Mission DataSoluTech (scénario fictif).** Le client, acteur du secteur médical, rencontre des problèmes de scalabilité sur ses traitements quotidiens. La solution proposée est une infrastructure NoSQL conteneurisée :

- **Migrer** un dataset médical (CSV ~55 000 lignes) vers MongoDB.
- **Conteneuriser** la base et le pipeline via Docker / Docker Compose.
- **Sécuriser** l'accès (authentification + rôles).
- **Tester** l'intégrité avant/après migration.
- **Documenter** une trajectoire d'évolution vers AWS (S3, RDS, DocumentDB, ECS).

**Compétences évaluées (RNCP39775BC02) :**
- Définir et formaliser les processus de traitement et de stockage des données.
- Mettre en place un système d'authentification afin de garantir la sécurité des données.
- Configurer l'environnement de travail.

---

## 2. Architecture

> Schéma à insérer ici (`docs/architecture.png`). *À compléter — produit à l'étape 2.*

Vue d'ensemble :  
┌────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  data/healthcare_  │ ──► │  Conteneur migrator  │ ──► │  Conteneur MongoDB   │
│   dataset.csv      │     │  (Python 3.x)        │     │  (auth activée)      │
│   (volume hôte)    │     │   - validation       │     │  Volume mongo_data   │
└────────────────────┘     │   - transformation   │     └──────────────────────┘
│   - insertion        │              ▲
│   - tests intégrité  │              │
└──────────────────────┘     ┌──────────────────────┐
│  MongoDB Compass     │
│  (host, port 27017)  │
└──────────────────────┘

**Composants Docker Compose :**
- `mongodb` : image `mongo:<version>` avec auth activée, volume nommé pour la persistance.
- `migrator` : image custom Python avec le script de migration et `requirements.txt`.
- (optionnel) `mongo-express` : interface web d'inspection (utile en dev).

**Volumes :**
- `mongo_data` (persistance des données MongoDB).
- bind mount `./data` (source CSV) → `/data` dans le conteneur migrator.

*Détails techniques justifiés dans [`DECISIONS.md`](./DECISIONS.md).*

---

## 3. Schéma de la base de données

> *À compléter à l'étape 1. Insérer un schéma `docs/schema_db.png` + description ci-dessous.*

**Base :** `healthcare`
**Collection :** `patients`

Champs prévus (à finaliser après exploration du CSV) :

| Champ | Type MongoDB | Description | Indexé |
|---|---|---|---|
| `_id` | ObjectId | Identifiant interne | oui (par défaut) |
| `name` | string | Nom du patient | non |
| `age` | int32 | Âge | oui (requêtes par tranche) |
| `gender` | string | Genre | non |
| `blood_type` | string | Groupe sanguin | oui |
| `medical_condition` | string | Pathologie | oui |
| `date_of_admission` | date | Date d'admission | oui |
| ... | ... | ... | ... |

**Index prévus** *(à justifier dans `DECISIONS.md`)* :
- Index simple sur `medical_condition`.
- Index composé `(date_of_admission, hospital)`.
- *À confirmer après analyse des cas d'usage.*

---

## 4. Sécurité — authentification et rôles

> *À implémenter à l'étape 1/2. Détailler ici la mise en œuvre concrète.*

**Authentification :** activée via `--auth` au démarrage de MongoDB. Tous les accès passent par un utilisateur authentifié.

**Rôles prévus** *(proposition, à valider) :*

| Rôle | Permissions | Usage |
|---|---|---|
| `admin_user` | `userAdminAnyDatabase`, `dbAdminAnyDatabase` | Administration uniquement |
| `migration_user` | `readWrite` sur `healthcare` | Utilisé par le script de migration |
| `analyst_user` | `read` sur `healthcare` | Consultation par les analystes |

**Gestion des secrets :**
- Credentials stockés dans `.env` (non versionné, voir `.gitignore`).
- Un fichier `.env.example` documente les variables attendues.
- Initialisation des utilisateurs via script `mongo-init/init-users.js` exécuté au premier démarrage du conteneur.

---

## 5. Prérequis

- **OS :** Windows 11 (testé), Linux/macOS supportés.
- **Docker Desktop** ≥ *À compléter*.
- **Docker Compose** v2+.
- **Git**.
- (Optionnel pour développement local hors conteneur) Python ≥ *À compléter* + MongoDB Compass.

---

## 6. Installation et lancement

```bash
# 1. Cloner le repo
git clone https://github.com/<USERNAME>/OPC5-Maintenez_et_documentez_un_systeme_de_stockage_des_donnees_securise_et_performant.git
cd OPC5-Maintenez_et_documentez_un_systeme_de_stockage_des_donnees_securise_et_performant

# 2. Récupérer le dataset
# Le dataset Kaggle n'est pas versionné. Le télécharger ici :
# https://www.kaggle.com/datasets/prasad22/healthcare-dataset
# puis placer healthcare_dataset.csv dans ./data/

# 3. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env pour définir les mots de passe.

# 4. Lancer la stack
docker compose up --build

# 5. Vérifier
# Le script migrator s'exécute, insère les données, lance les tests, puis termine.
# La collection est consultable via MongoDB Compass : mongodb://migration_user:<pwd>@localhost:27017/healthcare
```

**Arrêt et nettoyage :**

```bash
docker compose down          # arrête les conteneurs (volumes conservés)
docker compose down -v       # arrête et supprime les volumes (données perdues)
```

---

## 7. Logique de la migration

Le script `src/migrate.py` exécute la séquence suivante :

1. **Connexion MongoDB** avec timeout court (3s) — échoue vite si le serveur est inaccessible.
2. **Lecture du CSV** via pandas (`data/healthcare_dataset.csv` par défaut).
3. **Validation amont** : présence des 15 colonnes attendues, comptage des valeurs manquantes.
4. **Transformation** :
   - Renommage en snake_case (`Date of Admission` → `date_of_admission`).
   - Title Case sur `name` et `doctor` (le dataset source contient de la casse aléatoire).
   - Parsing explicite des dates (`%Y-%m-%d`).
   - Suppression des doublons stricts (~534 lignes sur 55 500).
5. **Chargement** :
   - Vidage de la collection avant insertion (idempotence).
   - Insertion par batchs de 5 000 (`insert_many` avec `ordered=False`).
6. **Indexation** : 4 index (cf. section 3). Créés **après** l'insertion pour ne pas ralentir le bulk load.
7. **Validation aval** : recompte, vérification de la présence de tous les index attendus.

Tous les événements sont logués en console **et** dans un fichier `logs/migration_YYYYMMDD_HHMMSS.log`.

**Volume traité** : 55 500 lignes en entrée → 54 966 documents en base après dédoublonnage. Migration en ~1,2 s en local.

### Démonstration CRUD

`src/crud.py` est un script pédagogique séparé qui démontre les 4 opérations CRUD sur des documents `Demo` isolés, et qui s'auto-nettoie (l'état final = état initial). Lancement : `uv run python -m src.crud`.

### Export

`src/export.py` extrait la collection vers deux formats complémentaires :
- `exports/patients_export.jsonl` — JSON Lines (un document par ligne, types Mongo préservés via extended JSON, ré-importable avec `mongoimport`).
- `exports/patients_export.csv` — CSV avec dates en ISO 8601, ouvrable dans Excel/Pandas.

Les outils standard Mongo ont également été testés : `mongoexport` (JSON et CSV), `mongodump` (BSON), `mongoimport` (réversibilité validée).

---

## 8. Tests

## 8. Tests

25 tests pytest répartis en 3 fichiers :

```bash
uv run pytest
```

| Fichier | Tests | Périmètre |
|---|---|---|
| `tests/test_csv_integrity.py` | 7 | Validation amont du CSV : structure, qualité, cohérence métier (dates, âges) |
| `tests/test_mongo_integrity.py` | 10 | Validation aval Mongo : comptage, typage (datetime/int/float), index présents, IXSCAN utilisé, doublons absents, Title Case appliqué |
| `tests/test_export.py` | 8 | Cohérence des fichiers exportés : comptage, JSON valide, header CSV complet, dates ISO |

Les fixtures partagées (`tests/conftest.py`) skippent proprement les tests si MongoDB est indisponible ou si la migration n'a pas été exécutée — pas de plantage en cascade.

**Pré-requis avant de lancer pytest** : avoir lancé au moins une fois `uv run python -m src.migrate` puis `uv run python -m src.export`.

---

## 9. Structure du dépôt


├── .gitignore  
├── .python-version  
├── README.md  
├── DECISIONS.md  
├── pyproject.toml  
├── uv.lock  
├── requirements.txt  
├── pytest.ini  
├── data/  
│   └── healthcare_dataset.csv     # non versionné  
├── notebooks/  
│   └── 01_exploration_dataset.ipynb  
├── src/  
│   ├── init.py  
│   ├── config.py                  # paramètres centralisés  
│   ├── migrate.py                 # pipeline CSV → MongoDB  
│   ├── export.py                  # pipeline MongoDB → JSONL/CSV  
│   └── crud.py                    # démonstration CRUD  
├── tests/  
│   ├── init.py  
│   ├── conftest.py  
│   ├── test_csv_integrity.py  
│   ├── test_mongo_integrity.py  
│   └── test_export.py  
├── exports/                       # non versionné (régénérable)  
└── logs/  

---

## 10. Recherches AWS

Documentation détaillée dans [`docs/aws_research.md`](./docs/aws_research.md). Couvre :
- Création d'un compte AWS.
- Modèles tarifaires.
- Amazon RDS et la question de MongoDB sur RDS.
- Amazon DocumentDB (compatibilité MongoDB).
- Déploiement via Amazon ECS.
- Sauvegardes et monitoring (CloudWatch, snapshots).

> ⚠️ Cette étape est documentaire — **aucun déploiement réel** n'est effectué dans ce projet.

---

## 11. Décisions techniques

L'ensemble des choix structurants (versions, rôles, indexation, format de logs, etc.) est tracé dans [`DECISIONS.md`](./DECISIONS.md). Ce fichier sert de support direct en soutenance pour défendre l'architecture.

---

## 12. Matrice consigne / livrables / preuves

| Élément de consigne | Livrable associé | Preuve à fournir | Statut |
|---|---|---|---|
| Lien GitHub | URL du repo | Lien dans la plateforme OC | ⏳ À produire au rendu |
| README détaillant la migration | `README.md` (ce fichier) | Section 7 + sections 2/3 | 🟡 En cours |
| `docker-compose.yml` | Fichier YAML racine | Fichier + démo `docker compose up` | ⏳ Étape 2 |
| Présentation PowerPoint | `docs/presentation.pptx` | Fichier + soutenance | ⏳ Étape 4 |
| Script(s) de migration | `src/migrate.py` | Script + démo locale | ⏳ Étape 1 |
| `requirements.txt` | Fichier racine | Fichier versionné | ⏳ Étape 1 |
| Tests d'intégrité automatisés | `tests/` + commande `pytest` | Sortie verte + rapport | ⏳ Étape 1 |
| Schéma BDD | `docs/schema_db.png` | Image insérée dans README §3 | ⏳ Étape 1 |
| Système d'authentification | Code + doc | README §4 + démo | ⏳ Étape 1/2 |
| Rôles utilisateurs | `mongo-init/init-users.js` | Fichier + démo (`db.getUsers()`) | ⏳ Étape 1/2 |
| Volumes Docker (≥ 1) | `docker-compose.yml` | Section `volumes:` | ⏳ Étape 2 |
| Recherches AWS | `docs/aws_research.md` | Document Markdown | ⏳ Étape 3 |
| Fiche d'autoévaluation | PDF complété | Document signé | ⏳ Étape 5 |

Légende : ✅ fait • 🟡 en cours • ⏳ à faire • ⚠️ à clarifier

---

## 13. État d'avancement

> Mis à jour à chaque jalon majeur.

- *À compléter au démarrage effectif du projet.*

---

## 14. Limites connues

| Étape | Statut | Date |
|---|---|---|
| Étape 1 — Migration MongoDB | ✅ Terminée | 2026-04-28 |
| Étape 2 — Conteneurisation Docker (auth + rôles) | ⏳ À démarrer | — |
| Étape 3 — Recherches AWS | ⏳ À démarrer | — |
| Étape 4 — Support de présentation | ⏳ À démarrer | — |
| Étape 5 — Autoévaluation | ⏳ À démarrer | — |

**Étape 1 livrée :**
- Pipeline complet `src/migrate.py` (extract → validate → transform → load → index → validate)
- Script d'export `src/export.py` (JSONL + CSV)
- Démonstration CRUD `src/crud.py` (Create/Read/Update/Delete idempotente)
- 25 tests pytest verts (CSV + Mongo + exports)
- Logs structurés horodatés
- Documentation des outils Mongo CLI testés (`mongoexport`, `mongodump`, `mongoimport`)

---

## 15. Auteur et contexte de formation

- **Auteur :** *Paul-Alexandre Annonay.*
- **Formation :** Data Engineer - OpenClassrooms.
- **Mentor :** *Paul Smadja*
- **Date de soutenance prévue :** *04/05/2026*