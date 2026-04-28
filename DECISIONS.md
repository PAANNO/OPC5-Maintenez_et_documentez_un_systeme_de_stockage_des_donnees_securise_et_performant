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

## [À compléter] — Choix de la version Python

**Contexte :** À décider au lancement effectif. Versions courantes au 28/04/2026 : 3.11, 3.12, 3.13.
**Options envisagées :** *À détailler.*
**Décision :** *À prendre.*
**Justification :** *À rédiger.*
**Alternatives écartées :** *À rédiger.*
**Impacts :** Image Docker de base, contraintes `requirements.txt`.

---

## [À compléter] — Choix du framework de tests (pytest vs unittest)

**Contexte :** L'étape 1 exige des tests automatisés. Les deux ressources fournies couvrent unittest et pytest.
**Options envisagées :** unittest (stdlib), pytest.
**Décision :** *À prendre — proposition : pytest.*
**Justification :** *À rédiger (syntaxe plus concise, fixtures plus puissantes, meilleur rapport, écosystème).*
**Impacts :** Dépendances `requirements.txt`, organisation `tests/`.

---

## [À compléter] — Stratégie d'authentification et de rôles MongoDB

**Contexte :** Compétence évaluée explicite. Boris demande nommément la description du système d'authentification et des rôles.
**Options envisagées :** Un seul rôle admin / 2 rôles (admin + applicatif) / 3 rôles (admin + r/w + r-o).
**Décision :** *À prendre — proposition : 3 rôles (admin_user, migration_user, analyst_user).*
**Justification :** *À rédiger (principe de moindre privilège, démontre la compréhension RBAC, facilite la défense en soutenance).*
**Impacts :** `mongo-init/init-users.js`, README §4, `.env.example`.

---

## [À compléter] — Stratégie d'indexation

**Contexte :** Point de vigilance explicite de l'étape 1.
**Options envisagées :** *À détailler après analyse du CSV et des cas d'usage.*
**Décision :** *À prendre.*

---