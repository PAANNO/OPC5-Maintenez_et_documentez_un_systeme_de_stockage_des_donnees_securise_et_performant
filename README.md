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
  - [8. Tests](#8-tests)
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

> *À compléter au fur et à mesure de l'implémentation.*

Le script `src/migrate.py` exécute la séquence suivante :

1. **Lecture du CSV** depuis `/data/healthcare_dataset.csv`.
2. **Validation amont** : vérification présence des colonnes attendues, types, valeurs manquantes (rapport pré-migration).
3. **Transformation** : typage explicite (dates, entiers), normalisation des chaînes, déduplication.
4. **Connexion à MongoDB** avec l'utilisateur `migration_user` (lecture du `.env`).
5. **Insertion** par batch dans `healthcare.patients` (`insert_many`).
6. **Création des index** (cf. section 3).
7. **Validation aval** : recompte, vérification d'échantillons, comparaison hashes/agrégats CSV vs Mongo.
8. **Rapport** : log structuré + écriture d'un résumé dans `logs/migration_<timestamp>.log`.

Opérations CRUD exposées (script + tests) :
- **Create** : `insert_one`, `insert_many`.
- **Read** : `find`, `find_one`, `aggregate`.
- **Update** : `update_one`, `update_many`.
- **Delete** : `delete_one`, `delete_many`.

---

## 8. Tests

> *À compléter à l'étape 1.*

Framework retenu : **`pytest`** *(justification dans `DECISIONS.md`)*.

```bash
# Lancer les tests dans le conteneur migrator
docker compose run --rm migrator pytest -v
```

Couverture prévue :
- Présence et type des colonnes du CSV source.
- Absence de doublons après migration.
- Égalité du nombre de documents insérés vs lignes CSV valides.
- Présence des index attendus.
- Authentification : un utilisateur sans droits ne peut pas écrire.

---

## 9. Structure du dépôt


>├── .env.example  
>├── .gitignore  
>├── README.md  
>├── DECISIONS.md  
>├── docker-compose.yml  
>├── Dockerfile.migrator  
>├── requirements.txt  
>├── data/  
>│   └── .gitkeep                    # le CSV >n'est pas versionné  
>├── mongo-init/  
>│   └── init-users.js               # création >des rôles au 1er démarrage  
>├── src/  
>│   ├── init.py  
>│   ├── migrate.py  
>│   ├── crud.py  
>│   └── config.py  
>├── tests/  
>│   ├── init.py  
>│   ├── test_integrity.py  
>│   └── test_crud.py  
>├── docs/  
>│   ├── architecture.png            # à >produire  
>│   ├── schema_db.png               # à >produire  
>│   └── aws_research.md             # étape 3  
>└── logs/  
>└── .gitkeep
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

> Section essentielle pour la soutenance. Mettre à jour au fil du projet.

- *À compléter.*

Pistes anticipées :
- Le dataset est synthétique (Kaggle), pas de données médicales réelles.
- Pas de réplication MongoDB configurée (mono-instance).
- Pas de TLS sur la connexion MongoDB locale (à mentionner pour la production).
- Pas de déploiement AWS effectif (hors périmètre).

---

## 15. Auteur et contexte de formation

- **Auteur :** *Paul-Alexandre Annonay.*
- **Formation :** Data Engineer - OpenClassrooms.
- **Mentor :** *Paul Smadja*
- **Date de soutenance prévue :** *04/05/2026*