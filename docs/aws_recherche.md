# Étape 3 — Exploration d'AWS

## 1. Contexte et objectif

Le client rencontre des limites de scalabilité sur la gestion quotidienne de ses données médicales. L'objectif de cette étape n'est pas de déployer la solution dans le cloud, mais d'identifier les services AWS les plus adaptés pour héberger, stocker, sauvegarder et superviser une architecture de données orientée MongoDB. Conformément à la consigne, l'architecture étudiée repose sur le déploiement d'une instance MongoDB dans un conteneur Docker sur Amazon ECS, accompagnée d'un conteneur dédié aux traitements de migration.

## 2. Pourquoi envisager un passage au cloud

Jusqu'à présent, la base de données MongoDB du projet est hébergée localement. Cette approche "on-premise" pose plusieurs limites lorsque le projet passe en production :

- **Disponibilité** : si le serveur local tombe en panne, l'application est indisponible.
- **Scalabilité** : augmenter la capacité demande l'achat et la configuration de nouveaux serveurs physiques.
- **Maintenance** : les sauvegardes, les mises à jour de sécurité et la supervision reposent entièrement sur l'équipe interne.
- **Coûts** : l'investissement initial (CapEx) est important et il faut dimensionner pour le pic, même si l'usage réel est plus faible la plupart du temps.

Le passage au cloud permet de gagner en élasticité, en résilience et en facilité d'exploitation. Les principaux bénéfices pour le client sont :

- **Élasticité** : on augmente ou réduit les ressources en quelques minutes selon les besoins.
- **Haute disponibilité** : les données peuvent être répliquées sur plusieurs zones géographiques.
- **Sécurité** : AWS gère une grande partie de la sécurité de l'infrastructure (modèle de responsabilité partagée).
- **Services managés** : plus besoin de gérer soi-même l'infrastructure sous-jacente.
- **Modèle économique OpEx** : on passe de lourds investissements matériels à une facturation mensuelle proportionnelle à l'usage.

## 3. Création et sécurisation d'un compte AWS

La création d'un compte AWS se fait depuis l'interface web AWS ; AWS précise qu'un compte standalone ne peut pas être créé via CLI ou API. La documentation officielle recommande ensuite un enchaînement simple : créer le compte, activer le MFA sur le root user, puis créer un utilisateur administrateur distinct pour les usages quotidiens.

### Prérequis
- Une adresse e-mail valide (qui servira d'identifiant root).
- Un numéro de téléphone.
- Une carte bancaire (obligatoire, même pour utiliser uniquement l'offre gratuite).
- Une pièce d'identité peut être demandée lors de la vérification.

### Étapes
1. Se rendre sur [https://aws.amazon.com](https://aws.amazon.com) et cliquer sur **"Créer un compte AWS"**.
2. Renseigner l'adresse e-mail, le mot de passe et le nom du compte.
3. Choisir le type de compte (Personnel ou Professionnel) et saisir ses coordonnées.
4. Renseigner les informations de carte bancaire (la carte ne sera pas débitée tant qu'on reste dans le **Free Tier**).
5. Vérifier l'identité par téléphone (SMS ou appel).
6. Choisir un plan de support (le plan **Basique** est gratuit et suffit pour explorer).
7. Se connecter à la **Console de gestion AWS**.

### Bonnes pratiques après création
- **Activer l'authentification multifacteur (MFA)** sur le compte root — AWS insiste particulièrement sur ce point.
- **Ne pas utiliser le compte root au quotidien** : créer un utilisateur IAM avec les droits adaptés.
- **Mettre en place un budget et des alertes de facturation** dans AWS Budgets pour éviter les mauvaises surprises.
- **Étiqueter (tagger) les ressources** pour suivre leurs coûts par projet.

## 4. Tarification d'AWS

### Les principes fondamentaux

AWS repose sur un modèle **pay-as-you-go** (paiement à l'usage) : on ne paie que les ressources réellement consommées, sans engagement ni coût initial. Ce modèle offre une grande souplesse et permet d'adapter la dépense aux variations d'activité.

Trois principes s'appliquent à la plupart des services :

1. **Paiement à l'usage** : facturation à l'heure, à la seconde, au Go stocké, ou à la requête effectuée.
2. **Économies d'échelle** : pour certains services, la tarification est dégressive — plus on consomme, moins le prix unitaire est élevé.
3. **Engagement = remise** : en s'engageant sur 1 ou 3 ans (via les *Savings Plans* ou *Reserved Instances*), on obtient jusqu'à **72 % de réduction** par rapport au tarif à la demande.

### Les principaux modèles de tarification pour le calcul

| Modèle | Principe | Usage recommandé |
|---|---|---|
| **On-Demand** | Paiement à l'heure/seconde, sans engagement | Charges variables, tests, développement |
| **Savings Plans / Reserved Instances** | Engagement 1 ou 3 ans, jusqu'à -72 % | Charges stables et prévisibles |
| **Spot Instances** | Capacité inutilisée d'AWS, jusqu'à -90 % | Traitements batch tolérants aux interruptions |

### Les postes de coûts à anticiper

Trois postes représentent l'essentiel de la facture :

- **Le calcul (compute)** : instances EC2, conteneurs ECS, Lambda. Dépend du type d'instance, de la région et du système d'exploitation.
- **Le stockage** : EBS, EFS, bases de données. Facturé au Go par mois.
- **Le transfert de données** : c'est le piège le plus fréquent. Le trafic **entrant** vers AWS est quasiment toujours gratuit, mais le trafic **sortant** vers Internet est facturé au Go.

### Estimation pour le projet

Il n'est pas pertinent de donner un prix fixe sans hypothèses précises, car le coût dépend notamment de la région AWS, de la taille des instances, du stockage, des sauvegardes, des E/S et du réseau. AWS fournit pour cela **AWS Pricing Calculator** ([https://calculator.aws](https://calculator.aws)), un outil web gratuit de planification permettant d'estimer les coûts avant déploiement.

### L'offre Free Tier

AWS propose un niveau gratuit qui permet d'expérimenter les services pendant 12 mois avec des limites mensuelles (par exemple 750 h d'instance EC2 t2.micro, 5 Go de stockage S3, etc.). Depuis mi-2025, les nouveaux comptes AWS reçoivent également jusqu'à **200 $ de crédits Free Tier** utilisables sur les services éligibles.

## 5. Amazon RDS et Amazon DocumentDB

### Amazon RDS ne supporte pas MongoDB

Une clarification s'impose d'emblée : **Amazon RDS (Relational Database Service) ne gère pas MongoDB**. RDS est un service dédié aux bases de données **relationnelles** et les moteurs officiellement pris en charge sont PostgreSQL, MySQL, MariaDB, Oracle, SQL Server et Db2. La formulation "RDS pour MongoDB" rencontrée dans le brief n'est donc pas techniquement exacte. Dans cette mission, Amazon RDS peut être présenté comme une solution de comparaison pour les bases relationnelles, mais pas comme une cible naturelle pour héberger MongoDB.

### Amazon DocumentDB (with MongoDB compatibility)

Amazon DocumentDB est le service AWS le plus proche de MongoDB. AWS le décrit comme un service fully managed permettant d'exécuter des applications avec les mêmes drivers et outils que ceux utilisés avec MongoDB, compatible avec les API MongoDB **3.6, 4.0, 5.0 et 8.0**.

**Caractéristiques principales :**

- **Entièrement managé** : AWS s'occupe des tâches de patching, de sauvegarde, de supervision et de scaling.
- **Haute disponibilité** : les données sont automatiquement répliquées sur trois zones de disponibilité.
- **Scalabilité** : un cluster peut contenir jusqu'à 16 instances (1 primaire + 15 répliques en lecture).
- **Sécurité** : chiffrement au repos (AWS KMS) et en transit (TLS), isolation dans un Amazon VPC, contrôle d'accès via IAM.

**Nuance importante :** DocumentDB est compatible MongoDB, mais n'est pas MongoDB à l'identique. Certaines fonctionnalités ne sont pas prises en charge ou le sont de façon limitée (capped collections, map-reduce, GridFS, recherche vectorielle avancée, données time-series, chiffrement côté client au niveau des champs). Pour ce projet, on retient donc DocumentDB comme point de comparaison, mais pas comme cible retenue. La consigne demande explicitement un déploiement de MongoDB dans un conteneur Docker sur ECS, ce qui permet de conserver une compatibilité **100 % MongoDB** et reste dans la continuité du travail Docker Compose réalisé à l'étape 2.

## 6. Déploiement d'une instance MongoDB dans un conteneur Docker sur Amazon ECS

### Qu'est-ce qu'Amazon ECS ?

**Amazon Elastic Container Service (ECS)** est un service d'orchestration de conteneurs entièrement managé qui permet de déployer, gérer et faire évoluer des applications conteneurisées (Docker). ECS propose deux modes de lancement :

- **EC2 launch type** : les conteneurs s'exécutent sur des instances EC2 qu'on provisionne et gère. Plus de contrôle, coût potentiellement plus bas pour des charges stables.
- **Fargate launch type** : mode **serverless** — AWS gère entièrement les serveurs sous-jacents. On ne paie que pour le CPU et la mémoire utilisés par les conteneurs. Recommandé pour simplifier l'exploitation.

### Architecture cible

L'architecture retenue pour ce projet déploie deux conteneurs sur un même cluster ECS :

- **Un conteneur MongoDB** qui héberge la base de données documentaire.
- **Un conteneur Python** dédié aux traitements de migration (lecture du CSV source, transformation, insertion dans MongoDB).

```
        VPC
        │
        ├── Cluster ECS
        │   │
        │   ├── Tâche ECS : conteneur Python (migration)
        │   │         │
        │   │         ▼
        │   └── Tâche ECS : conteneur MongoDB ── volume EFS (persistance)
        │
        └── CloudWatch (logs + métriques)
```

### Les étapes du déploiement

1. **Créer un VPC** avec des sous-réseaux sur plusieurs zones de disponibilité.
2. **Créer un cluster ECS** (Fargate recommandé pour éviter la gestion de serveurs).
3. **Préparer les images Docker** :
   - Image officielle `mongo` depuis Docker Hub pour le conteneur de base de données.
   - Image personnalisée pour le conteneur Python de migration, stockée dans **Amazon ECR** (Elastic Container Registry).
4. **Configurer le stockage persistant** : les conteneurs sont éphémères. Pour persister les données MongoDB, monter un volume **Amazon EFS** sur `/data/db` dans le conteneur MongoDB.
5. **Créer les Task Definitions** qui décrivent pour chaque conteneur :
   - L'image Docker à utiliser (ex. `mongo:7` pour la base).
   - Les ressources CPU/mémoire.
   - Le mode réseau (`awsvpc` pour Fargate).
   - Les variables d'environnement (identifiants, nom de BDD, chaîne de connexion pour le conteneur de migration).
   - Les volumes montés (EFS pour MongoDB).
   - Les rôles IAM d'exécution.
6. **Créer un Service ECS** pour le conteneur MongoDB, qui le maintient en permanence en exécution. Le conteneur de migration peut être lancé comme une **tâche ponctuelle** (Run Task) ou planifiée via EventBridge.
7. **Configurer la sécurité** :
   - Security Groups restreignant les accès réseau entre conteneurs.
   - Stockage des mots de passe dans **AWS Secrets Manager** (jamais en dur dans la task definition).
   - Chiffrement du volume EFS au repos avec KMS.
8. **Configurer la journalisation** : envoyer les logs des deux conteneurs vers **Amazon CloudWatch Logs**.

### Points d'attention

- **MongoDB est stateful** : le stockage persistant via EFS est indispensable, sinon les données sont perdues à chaque redémarrage du conteneur.
- **Haute disponibilité** : pour la production, il faudrait envisager un **replica set MongoDB** (1 primaire + 2 secondaires) sur différentes zones de disponibilité.
- **Sauvegardes** : EFS seul ne suffit pas, il faut mettre en place une stratégie de sauvegarde dédiée.
- **Gestion manuelle** : contrairement à un service managé, toute la maintenance (patchs, monitoring fin, failover) reste à la charge de l'équipe.

## 7. Sauvegardes et surveillance

### Configuration des sauvegardes

Pour une instance MongoDB conteneurisée sur ECS, les sauvegardes ne sont **pas automatiques** : il faut les mettre en place explicitement. Plusieurs approches peuvent se combiner :

- **Snapshots EFS via AWS Backup** : AWS Backup est un service centralisé qui permet d'orchestrer les sauvegardes de plusieurs services AWS (dont EFS) avec des politiques communes et une conservation longue durée. On peut définir une fréquence (ex. quotidienne) et une rétention (ex. 30 jours).
- **mongodump planifié** : un job ECS programmé via **EventBridge** peut lancer régulièrement un `mongodump` et déposer l'export dans un bucket **S3** pour archivage.
- **Tests de restauration** : il est essentiel de tester régulièrement la restauration des sauvegardes — une sauvegarde non testée est une sauvegarde qui n'existe pas.

### Supervision (monitoring)

**Amazon CloudWatch** est le service central de supervision AWS. Il collecte automatiquement les métriques et logs des conteneurs ECS :

- **Métriques** : CPU, mémoire, utilisation réseau des tâches ECS, espace disque EFS.
- **Logs** : logs applicatifs des deux conteneurs (MongoDB et Python de migration) centralisés dans CloudWatch Logs.
- **Alarmes** : déclenchent une notification (via SNS → e-mail, SMS, Slack) ou une action automatique lorsqu'un seuil est franchi.
- **Tableaux de bord** : visualisations personnalisées regroupant les métriques clés.

Pour aller plus loin sur la surveillance de MongoDB lui-même, on peut également envoyer des métriques spécifiques (nombre de connexions, latence des requêtes, taille des collections) vers CloudWatch via un exporter ou un script custom dans le conteneur.

**Services complémentaires utiles :**

- **AWS CloudTrail** : journalise toutes les actions effectuées sur les services AWS (qui a fait quoi, quand). Essentiel pour l'audit et la sécurité.
- **AWS Health Dashboard** : notifie les événements de maintenance et incidents AWS pouvant impacter les services.

### Bonnes pratiques

- Mettre en place des alarmes **CPU élevé**, **mémoire saturée**, **espace EFS faible**.
- Centraliser les logs des deux conteneurs dans CloudWatch pour faciliter le débogage.
- Configurer une **rotation automatique des identifiants** via AWS Secrets Manager.
- Documenter un **plan de reprise d'activité (PRA)** avec RTO (temps de reprise) et RPO (perte de données acceptable) clairs.

## 8. Ouverture : une architecture alternative à considérer

Une évolution intéressante de cette architecture, à discuter avec le client pour une future phase, consisterait à remplacer la gestion manuelle de MongoDB par une combinaison de services AWS managés : **Amazon S3** pour stocker les fichiers bruts (CSV sources, exports, archives) grâce à sa durabilité de 99,999999999 %, **Amazon ECS** conservé pour exécuter le conteneur Python de migration, et **Amazon DocumentDB** comme cible de base documentaire managée compatible MongoDB. Cette architecture apporterait plusieurs avantages : suppression de la charge d'exploitation de MongoDB (patchs, sauvegardes, failover gérés par AWS), haute disponibilité native via la réplication multi-AZ automatique de DocumentDB, séparation claire entre stockage de fichiers, calcul et base de données, et meilleure résilience en cas de panne d'un composant. Elle resterait compatible avec le travail Docker déjà réalisé, puisque seul le conteneur MongoDB serait remplacé par un service managé. Le principal arbitrage à faire concerne la compatibilité partielle de DocumentDB avec MongoDB : il faudrait vérifier que les fonctionnalités utilisées par le projet sont bien supportées avant toute bascule.

## 9. Conclusion

Le cloud AWS offre plusieurs services pertinents pour répondre au besoin du client. Dans le cadre de ce projet et conformément à la consigne, l'architecture retenue repose sur le déploiement d'une instance MongoDB dans un conteneur Docker sur Amazon ECS, accompagnée d'un conteneur dédié aux traitements de migration. Cette approche présente plusieurs avantages : elle reste dans la continuité directe du travail Docker Compose réalisé à l'étape 2, elle garantit une compatibilité 100 % MongoDB, et elle permet de maîtriser l'ensemble de la configuration. En contrepartie, elle demande une gestion manuelle des sauvegardes, de la haute disponibilité et du monitoring spécifique à MongoDB. La formulation "RDS pour MongoDB" doit être corrigée puisque RDS ne supporte pas ce moteur, et une alternative S3 + ECS + DocumentDB pourrait être envisagée dans une phase ultérieure pour réduire la charge d'exploitation. Dans tous les cas, la mise en place d'une stratégie de sauvegardes via AWS Backup, d'une supervision CloudWatch et d'un budget AWS restent des prérequis à ne pas négliger avant tout passage en production.

---

## Sources

- [Documentation officielle Amazon ECS](https://aws.amazon.com/ecs/)
- [Amazon DocumentDB](https://aws.amazon.com/documentdb/)
- [Tarification AWS](https://aws.amazon.com/pricing/)
- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Backup](https://aws.amazon.com/backup/)
- [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/)
- [Amazon EFS](https://aws.amazon.com/efs/)