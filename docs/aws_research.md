# Recherches AWS — Étape 3 du projet OPC5

> **Périmètre :** étape documentaire.  
> **Objectif :** documenter les services AWS pertinents pour faire évoluer la stack DataSoluTech vers une infrastructure cloud managée.  
> **Posture :** document neutre informatif. Aucun déploiement réel.

---

## Sommaire

- [1. Introduction](#1-introduction)
- [2. Création d'un compte AWS](#2-création-dun-compte-aws)
- [3. Tarification AWS](#3-tarification-aws)
- [4. Amazon RDS et la question MongoDB](#4-amazon-rds-et-la-question-mongodb)
- [5. Amazon DocumentDB](#5-amazon-documentdb)
- [6. Amazon ECS — déploiement de conteneurs](#6-amazon-ecs--déploiement-de-conteneurs)
- [7. Sauvegardes et monitoring](#7-sauvegardes-et-monitoring)
- [8. Synthèse](#8-synthèse)
- [Sources et références](#sources-et-références)

---

## 1. Introduction

Le présent document fait suite à la mise en place de l'environnement local de gestion des données médicales chez DataSoluTech (cf. [README](../README.md)). Il vise à éclairer les options offertes par Amazon Web Services pour faire évoluer cette stack vers une infrastructure cloud managée, en cohérence avec les enjeux de scalabilité, de sécurité et de continuité d'activité identifiés en début de mission.

Cinq sujets sont traités : la création et la prise en main d'un compte AWS, le modèle de tarification, les services managés Amazon RDS et Amazon DocumentDB, le déploiement de conteneurs Docker sur Amazon ECS, et la configuration des sauvegardes et de la supervision des bases de données.

Ce document est exclusivement documentaire et ne s'accompagne d'aucun déploiement effectif. Il a vocation à servir de base de discussion technique pour cadrer la trajectoire cloud du projet.

---

## 2. Création d'un compte AWS

<!--
À COUVRIR :
- Procédure pas à pas (étapes principales, pas un tuto exhaustif)
- Pré-requis : email, carte bancaire (même pour le free tier !)
- Vérification téléphone, choix du plan support (Basic = gratuit, suffisant ici)

POINTS DE SÉCURITÉ ESSENTIELS À DOCUMENTER :
- Différence root account vs IAM users (NE JAMAIS utiliser le root pour les opérations courantes)
- Activer MFA sur le root account dès la création
- Créer un utilisateur IAM admin pour l'usage quotidien
- Configurer les alertes facturation (CloudWatch Billing Alarm) — éviter les mauvaises surprises

CONTEXTE PERSONNEL À MENTIONNER :
- "J'ai créé mon compte le [DATE]" (à compléter)
- Statut free tier : actif jusqu'à [DATE+12 MOIS]
- Captures d'écran possibles : page d'accueil console AWS, dashboard IAM (sans données sensibles)

SOURCES :
- https://aws.amazon.com/fr/free/
- https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- https://aws.amazon.com/fr/getting-started/

LONGUEUR CIBLE : 1 page (~30 lignes)
-->

*[À rédiger]*

### 2.1 Procédure de création

*[À rédiger]*

### 2.2 Bonnes pratiques de sécurité initiale

*[À rédiger]*

### 2.3 Statut de mon compte

*[À rédiger]*

---

## 3. Tarification AWS

<!--
À COUVRIR :
- Modèle "pay as you go" : tu ne paies que ce que tu consommes
- Pas d'abonnement obligatoire, pas de frais de mise en service

LES 3 LEVIERS DE COÛT À EXPLIQUER :
1. Compute (vCPU/h, RAM/h pour EC2, ECS Fargate, etc.)
2. Storage (Go/mois pour EBS, S3, DocumentDB volume...)
3. Data transfer (sortie internet payante, entrée et inter-AZ même VPC souvent gratuites)

FREE TIER (À DÉTAILLER) :
- 12 months free : EC2 t2.micro, RDS db.t2.micro, S3 5 Go, etc.
- Always free : Lambda 1M req/mois, DynamoDB 25 Go, CloudWatch 10 métriques, etc.
- Trials : 30 jours sur certains services

OUTILS À MENTIONNER :
- AWS Pricing Calculator (estimer AVANT) : https://calculator.aws/
- AWS Cost Explorer (suivre APRÈS)
- Billing Dashboard

OPTIONS D'OPTIMISATION (mention rapide) :
- Reserved Instances (engagement 1-3 ans, -30% à -75%)
- Savings Plans (engagement plus flexible)
- Spot Instances (capacité non-garantie, jusqu'à -90%)

⚠️ Vérifier les prix en EUR/zone eu-west-3 (Paris) ou eu-west-1 (Irlande) qui sont les plus pertinentes pour un client français.

SOURCES :
- https://aws.amazon.com/fr/pricing/
- https://aws.amazon.com/fr/free/
- AWS Whitepaper "How AWS Pricing Works" (PDF officiel)

LONGUEUR CIBLE : 1.5 pages (~50 lignes)
-->

*[À rédiger]*

### 3.1 Le modèle « pay as you go »

*[À rédiger]*

### 3.2 Les trois leviers de coût

*[À rédiger]*

### 3.3 Le free tier

*[À rédiger — tableau possible]*

### 3.4 Outils d'estimation et de suivi

*[À rédiger]*

### 3.5 Optimisations possibles (mention)

*[À rédiger]*

---

## 4. Amazon RDS et la question MongoDB

<!--
SOUS-OBJECTIF PÉDAGOGIQUE MASQUÉ DE LA CONSIGNE :
La consigne dit "Amazon RDS pour MongoDB" — c'est un piège volontaire.
RDS ne supporte PAS MongoDB. Le vrai service AWS managé MongoDB-compatible est DocumentDB.
Cette section doit donc :
1. Présenter RDS (service managé pour SGBDR)
2. Lister ses moteurs supportés
3. Conclure clairement : "MongoDB n'est pas dans cette liste, donc pour Mongo managé sur AWS, on regarde DocumentDB → cf. section suivante"

À COUVRIR :
- Qu'est-ce qu'un service "managé" (l'opposé de self-hosted) : AWS gère l'OS, les patches, la HA, les backups
- Moteurs supportés par RDS : MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Aurora (compatible MySQL/PostgreSQL)
- Ce que RDS ne fait PAS : NoSQL en général
- Pour les SGBDR : pourquoi RDS plutôt que self-hosted ? (HA, backups auto, Read Replicas, Multi-AZ)

LONGUEUR CIBLE : 0.5-1 page (~25 lignes)
La section est volontairement courte : c'est surtout un aiguillage vers DocumentDB.

SOURCES :
- https://aws.amazon.com/fr/rds/
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.html
-->

*[À rédiger]*

### 4.1 Qu'est-ce qu'Amazon RDS ?

*[À rédiger]*

### 4.2 Moteurs supportés

*[À rédiger]*

### 4.3 Pourquoi MongoDB n'est pas sur RDS

*[À rédiger]*

---

## 5. Amazon DocumentDB

<!--
C'EST LA SECTION CLÉ DU DOCUMENT.
DocumentDB = service AWS managé compatible avec l'API MongoDB.
Important pour DataSoluTech : c'est le "RDS-like" pour MongoDB.

À COUVRIR :
- Présentation : NoSQL document-oriented, API compatible MongoDB
- Compatibilité : compatible MongoDB 3.6, 4.0, 5.0 (vérifier le statut actuel — la liste évolue)
- LIMITATION IMPORTANTE : ce n'est PAS du vrai MongoDB derrière. AWS a réimplémenté l'API.
  Conséquence : certaines opérations Mongo récentes ne sont pas supportées.
  Voir la liste officielle des "Functional Differences" : https://docs.aws.amazon.com/documentdb/latest/developerguide/functional-differences.html

ARCHITECTURE INTERNE (à vulgariser) :
- Séparation compute / storage (cluster avec instances primaires + réplicas en lecture)
- Storage auto-scalé jusqu'à 64 TiB
- Backup continu vers S3, point-in-time recovery (35 jours par défaut)
- Multi-AZ par design (réplication synchrone sur 6 copies)

CAS D'USAGE :
- Quand DocumentDB est pertinent (charge productive, équipe sans expertise ops Mongo, exigence HA)
- Quand DocumentDB n'est PAS pertinent (besoin de fonctions Mongo récentes, budget serré, faible volume)
- Alternatives : MongoDB Atlas (sur AWS, géré par MongoDB Inc., plus de fonctionnalités), self-hosted sur EC2

POUR DATASOLUTECH (ne pas formuler comme une recommandation explicite) :
- Identifier ce que MongoDB Atlas et DocumentDB apportent par rapport au self-hosted
- Mentionner que le client devrait comparer en fonction de ses propres exigences

LONGUEUR CIBLE : 2 pages (~60 lignes)

SOURCES :
- https://aws.amazon.com/fr/documentdb/
- https://docs.aws.amazon.com/documentdb/latest/developerguide/what-is.html
- https://docs.aws.amazon.com/documentdb/latest/developerguide/functional-differences.html
- https://www.mongodb.com/atlas (pour la comparaison)
-->

*[À rédiger]*

### 5.1 Présentation

*[À rédiger]*

### 5.2 Compatibilité MongoDB

*[À rédiger]*

### 5.3 Architecture interne

*[À rédiger]*

### 5.4 Cas d'usage et limites

*[À rédiger]*

### 5.5 Alternatives à considérer

*[À rédiger]*

---

## 6. Amazon ECS — déploiement de conteneurs

<!--
RAPPEL CONSIGNE : "Déploiement d'une instance MongoDB dans un conteneur Docker sur Amazon ECS"
Cette formulation est étrange — déployer Mongo en conteneur sur ECS est une option,
mais souvent on combine ECS pour le compute applicatif + DocumentDB pour la donnée.

À COUVRIR :
- Qu'est-ce qu'ECS : service AWS d'orchestration de conteneurs Docker
- Alternative managée à Kubernetes (qui s'appelle EKS sur AWS)
- Plus simple qu'EKS, suffisant pour des cas d'usage classiques

CONCEPTS CLÉS À EXPLIQUER :
- **Cluster** : groupe logique de ressources (équivalent du nœud Compose en plus grand)
- **Task Definition** : la "recette" d'un conteneur (image, ressources, env vars, ports)
   = équivalent ECS du service dans docker-compose.yml
- **Task** : une instance running d'une task definition
- **Service** : maintient un nombre voulu de tasks running, gère la résilience
- **Launch type** :
  - **Fargate** (serverless, AWS gère les instances sous-jacentes)
  - **EC2** (tu gères tes propres instances, plus complexe mais moins cher à grande échelle)

POUR LE PIPELINE DATASOLUTECH :
- Le `migrator` actuel pourrait facilement tourner en task ECS Fargate
- Mais MongoDB en conteneur sur ECS pose des questions : où est le volume persistant ?
  - EBS attaché à une task : possible mais complexe (EBS = AZ-locked)
  - EFS (NFS) : possible aussi, plus simple côté lifecycle
  - Mais en pratique, on préfère DocumentDB pour la donnée et ECS pour les workers
- Architecture cible théorique : S3 (CSV source) → ECS Fargate (migrator) → DocumentDB (data)

SCHÉMA À PRODUIRE (placeholder) :
À ce stade, juste mentionner qu'un schéma d'architecture cible serait pertinent.
Tu pourras le produire en étape 4 (présentation) où c'est plus utile.

LONGUEUR CIBLE : 1.5 pages (~45 lignes)

SOURCES :
- https://aws.amazon.com/fr/ecs/
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html
- "ECS vs EKS vs Fargate" (chercher des comparatifs récents)
-->

*[À rédiger]*

### 6.1 Qu'est-ce qu'Amazon ECS ?

*[À rédiger]*

### 6.2 Concepts clés

*[À rédiger]*

### 6.3 Fargate vs EC2

*[À rédiger]*

### 6.4 Application au cas DataSoluTech

*[À rédiger]*

---

## 7. Sauvegardes et monitoring

<!--
DEUX VOLETS DISTINCTS À COUVRIR.

=== SAUVEGARDES ===

POUR DOCUMENTDB :
- Snapshots automatiques quotidiens (rétention 1-35 jours, 1 par défaut)
- Snapshots manuels possibles à tout moment
- Point-in-time recovery (PITR) jusqu'à la seconde près sur les 35 derniers jours

POUR LES VOLUMES EBS (si conteneur Mongo sur ECS) :
- Snapshots EBS, stockés dans S3, incrémentaux
- AWS Backup pour automatiser la politique de rétention

POUR S3 :
- Versioning : conserver les anciennes versions des objets
- Lifecycle rules : déplacer automatiquement vers S3 Glacier après N jours

=== MONITORING ===

CLOUDWATCH METRICS :
- Métriques par service (CPU, RAM, IOPS, latence...) toutes les 1-5 min
- Alarmes : alertes par email/SMS quand un seuil est franchi
- Custom metrics possibles (ton app pousse ses propres métriques)

CLOUDWATCH LOGS :
- Centralisation des logs de tous les services AWS
- Recherche, filtres, alertes basées sur le contenu
- Pour ECS : driver de logs `awslogs` envoie tout sur CloudWatch

DOCUMENTDB PERFORMANCE INSIGHTS :
- Tableau de bord dédié : top requêtes lentes, charge par utilisateur, etc.
- Outil indispensable en production

BONNES PRATIQUES À ÉNONCER :
- 3 types d'alertes critiques : facturation, performance, sécurité
- Tester les restaurations régulièrement (un backup non testé n'existe pas)

LONGUEUR CIBLE : 1.5 pages (~45 lignes)

SOURCES :
- https://docs.aws.amazon.com/documentdb/latest/developerguide/backup_restore.html
- https://aws.amazon.com/fr/cloudwatch/
- https://aws.amazon.com/fr/backup/
-->

*[À rédiger]*

### 7.1 Sauvegardes

*[À rédiger]*

### 7.2 Monitoring avec CloudWatch

*[À rédiger]*

### 7.3 Bonnes pratiques

*[À rédiger]*

---

## 8. Synthèse

<!--
SECTION DE FERMETURE.

CONTENU SUGGÉRÉ :
- Tableau récapitulatif "Pour faire X chez AWS, j'utilise Y"
  Ex :
  | Besoin | Service AWS |
  |---|---|
  | Stocker des fichiers (CSV source) | S3 |
  | Faire tourner le pipeline conteneurisé | ECS Fargate |
  | Héberger MongoDB managé | DocumentDB |
  | Sauvegardes automatisées | Snapshots DocumentDB + AWS Backup |
  | Monitoring | CloudWatch |
  | Secrets et credentials | AWS Secrets Manager |

- Renvoyer vers README et DECISIONS.md pour boucler le projet
- Mention claire que cette étape n'a PAS donné lieu à un déploiement réel

LONGUEUR CIBLE : 0.5 page
-->

*[À rédiger]*

---

## Sources et références

<!--
Lister ici les sources utilisées au fil de la rédaction.
Catégoriser pour faciliter la consultation.
-->

### Documentation AWS officielle

- *[À compléter]*

### Articles et tutoriels

- *[À compléter]*

### Comparatifs externes

- *[À compléter]*

---

*Document rédigé dans le cadre du projet OPC5 — formation Data Engineer OpenClassrooms.*  
*Auteur : Paul-Alexandre Annonay.*  
*Dernière mise à jour : 29/04/2026.*