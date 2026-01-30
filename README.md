# <NOM_DU_PROJET> – Parcours Data Engineer OpenClassrooms

Template de dépôt pour les projets du parcours Data Engineer OpenClassrooms.
Remplace les éléments entre <...> par les informations de ton projet.

## 🎯 Objectifs du projet

Résumé en quelques lignes :
- Quel est le problème à résoudre ?
- Quel est le livrable principal (pipeline ETL, dashboard, modèle, data warehouse, etc.) ?
- Quel est le rôle joué (Data Engineer dans une équipe X, pour l’entreprise Y…) ?

## 🧩 Contexte

Expliquer brièvement :
- Le contexte métier (secteur, enjeux business)
- Le contexte technique (données disponibles, contraintes)
- Le cadre OpenClassrooms (nom du projet, session, mentor si besoin)

## 🎓 Compétences évaluées (brief OC)

Lister ici les compétences indiquées dans le sujet :
- Exemple : Mettre en place un environnement de développement pour la data
- Exemple : Modéliser et implémenter une base de données
- Exemple : Concevoir des pipelines de données robustes

## 🏗️ Architecture du projet

Décrire les grandes briques :
- Sources de données (fichiers CSV, API, base SQL…)
- Étapes du pipeline (ingestion, nettoyage, transformation, chargement…)
- Stockage cible (data warehouse, base analytique, fichiers parquet…)
- Outils utilisés (Python, SQL, Spark, Airbyte, Kestra, Docker…)

Tu peux ajouter un schéma dans `docs/` et le référencer ici :

```mermaid
flowchart LR
    A[Source de données] --> B[Ingestion]
    B --> C[Nettoyage / transformation]
    C --> D[Base de données / Datalake]
    D --> E[Consommation (BI / analyse)]
```

## 🛠️ Stack technique

- Langage : Python 3.14
- Environnement de développement : VS Code + extensions (Python, Jupyter, etc.)
- GGestion de version : Git & GitHub
- Base(s) de données : `<PostgreSQL / MySQL / SQL Server / autre>`
- Traitements de données : `<Pandas / PySpark / dbt / autres>`
- Orchestration / ingestion : `<Airbyte / Kestra / Airflow / scripts maison…>`
- Conteneurisation (si utilisé) : Docker, Docker Compose

Adapter la liste en fonction du projet.

## 📂 Structure du dépôt

```txt
.
├─ .vscode/
│  └─ settings.json
├─ data/
│  ├─ raw/        # données brutes (fichiers fournis par OC, exports, etc.)
│  ├─ processed/  # données nettoyées / transformées
│  └─ external/   # sources externes (APIs, autres jeux de données)
├─ docs/          # schémas, compte-rendus, notes, exports de diagrammes
|  ├─ Livrables/
├─ notebooks/     # notebooks Jupyter d'exploration / POC
├─ src/
│  └─ project_name/      # à renommer pour chaque projet
│      ├─ __init__.py
│      ├─ config/        # fichiers de config (YAML/JSON)
│      └─ pipelines/     # scripts ETL, jobs, traitements
├─ tests/         # tests unitaires / d’intégration
├─ .gitignore
├─ README.md
├─ requirements.txt
└─ LICENSE        # optionnel (MIT par ex.)
```
Remplacer `<project_name>` par un nom de package adapté au projet
(ex. : `customer_churn`, `etl_orders`, `log_processing`, etc.).

## 🚀 Installation & exécution

### 1. Prérequis

- Python 3.14
- Git installé
- (Optionnel) Docker / Docker Compose
- Accès aux données si elles ne sont pas versionnées (voir section `data/`)

### 2. Cloner le dépôt
```bash
git clone https://github.com/<ton-compte>/<nom-du-repo>.git
cd <nom-du-repo>
```
### 3. Créer et activer l'environnement virtuel
```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

#macOS / Linux
source .venv/bin/activate
```
### 4. Installer les dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
### 5. Lancer les notebooks

Dans VS Code :
1. Ouvrir le dossier du projet.
2. Sélectionner l’interpréteur Python pointant vers `.venv`.
3. Ouvrir un notebook dans `notebooks/`.
4. Choisir le kernel correspondant à `.venv`.

### 6. Lancer le code Python
```bash
python -m <project_name>.pipelines.main
```
(À adapter selon ton point d'entrée.)

## ✅ Qualité, formatage & tests

### Formatage

Le projet utilise Black pour formater le code :

```bash
black src tests
```
### Tests

Les tests sont basés sur `pytest` :
```bash
pytest
```
## 📎 Livrables OpenClassrooms
- Code source dans ce dépôt Git
- Rapport / présentation : voir dossier docs/
- (Selon le projet) exports de données, captures d’écran, schémas d’architecture

## ✍️ Auteur
- Nom : Paul-Alexandre ANNONAY
- Parcours : Data Engineer – OpenClassrooms
- Email : pa.annonay@gmail.com

### b) `.gitignore` (Python + notebooks)

```gitignore
# Environnements virtuels
.venv/
env/
venv/

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.pdb

# Jupyter
.ipynb_checkpoints/

# Données volumineuses / temporaires
data/raw/
data/processed/
data/external/

# Logs / sorties
logs/
*.log

# OS
.DS_Store
Thumbs.db

# VS Code
.vscode/*
!.vscode/settings.json
```

Tu pourras enlever data/raw/ du .gitignore si, pour un projet, OC te demande explicitement de versionner les données.

### c) `requirements.txt` – base pour un projet data engineer
```txt
# Core
python-dotenv

# Data manipulation
pandas
numpy

# BDD / SQL
sqlalchemy
psycopg2-binary  # si tu utilises PostgreSQL

# Notebooks
jupyter
ipykernel

# Qualité
black
pytest

# À compléter selon le projet :
# pyspark
# kafka-python
# requests
# pydantic
```
Pour chaque projet, tu ajoutes / retires les libs selon le brief.

### d) `.vscode/settings.json` – pour que VS Code soit nickel
```js
{
  // Interpréteur Python : le .venv du projet
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",

  // Sur Windows, si le chemin ci-dessus pose problème, tu peux le remplacer par :
  // "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",

  // Formatage automatique
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },

  // Masquer certains dossiers dans l'explorateur
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true
  },

  // Jupyter: utiliser le kernel associé à l'interpréteur sélectionné
  "jupyter.jupyterServerType": "local"
}
```

Pour t’éviter de dupliquer les réglages selon l’OS, tu peux aussi simplement laisser VS Code détecter l’interpréteur et ne garder que la partie formatage :

```json
{
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true
  }
}
```