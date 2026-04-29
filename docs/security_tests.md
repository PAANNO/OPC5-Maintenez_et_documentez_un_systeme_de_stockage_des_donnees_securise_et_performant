# Tests de sécurité — Étape 2

> Validation manuelle de l'authentification MongoDB et du principe du moindre privilège.
> Date : 2026-04-28
> Environnement : Docker Compose, MongoDB 8.2.7, Windows 11.

## Pré-requis

Stack démarrée :
```bash
docker compose up -d
docker compose ps
# opc5-mongodb : Up (healthy)
# opc5-migrator : Exited (0)
```

---

## Test 1 — Lister les utilisateurs (admin)

**Objectif :** vérifier que `init-users.js` a créé les deux comptes applicatifs.

**Commande :**
```powershell
docker exec opc5-mongodb mongosh --quiet `
  -u admin -p adminPwd2026! --authenticationDatabase admin `
  --eval "db.getSiblingDB('healthcare_db').getUsers()"
```

**Sortie :**
```
{
  users: [
    {
      _id: 'healthcare_db.analyst_user',
      userId: UUID('a587e025-e7ba-4c78-9934-1212a472ad9c'),
      user: 'analyst_user',
      db: 'healthcare_db',
      roles: [ { role: 'read', db: 'healthcare_db' } ],
      mechanisms: [ 'SCRAM-SHA-1', 'SCRAM-SHA-256' ]
    },
    {
      _id: 'healthcare_db.migration_user',
      userId: UUID('32763d9a-2191-4dac-949f-1afea2bf3589'),
      user: 'migration_user',
      db: 'healthcare_db',
      roles: [ { role: 'readWrite', db: 'healthcare_db' } ],
      mechanisms: [ 'SCRAM-SHA-1', 'SCRAM-SHA-256' ]
    }
  ],
  ok: 1
}
```
**Résultat :** `migration_user` (readWrite) et `analyst_user` (read) présents sur `healthcare_db`.

---

## Test 2 — Accès anonyme refusé

**Objectif :** prouver que l'authentification est réellement active.

**Commande :**
```powershell
docker exec opc5-mongodb mongosh --quiet `
  --eval "db.getSiblingDB('healthcare_db').patients.countDocuments()"
```

**Sortie :**
```
MongoServerError: Command aggregate requires authentication
```

**Résultat :** Erreur `Unauthorized` comme attendu — aucun accès sans credentials.

---

## Test 3 — `migration_user` (readWrite) lit la collection

**Commande :**
```powershell
docker exec opc5-mongodb mongosh --quiet `
  -u migration_user -p migrationPwd2026! `
  --authenticationDatabase healthcare_db `
  --eval "db.getSiblingDB('healthcare_db').patients.countDocuments()"
```

**Sortie :**
```
54966
```

**Résultat :** 54966 documents — lecture OK avec le user d'application.

---

## Test 4 — `analyst_user` (read) : moindre privilège

### 4a — Lecture autorisée

**Commande :**
```powershell
docker exec opc5-mongodb mongosh --quiet `
  -u analyst_user -p analystPwd2026! `
  --authenticationDatabase healthcare_db `
  --eval "db.getSiblingDB('healthcare_db').patients.countDocuments()"
```

**Sortie :**
```
54966
```

**Résultat :** 54966 — lecture OK.

### 4b — Écriture refusée (preuve du moindre privilège)

**Commande :**
```powershell
docker exec opc5-mongodb mongosh --quiet `
  -u analyst_user -p analystPwd2026! `
  --authenticationDatabase healthcare_db `
  --eval "db.getSiblingDB('healthcare_db').patients.insertOne({test: 'should fail'})"
```

**Sortie :**
```
MongoServerError: not authorized on healthcare_db to execute command { insert: "patients", documents: [ { test: "should fail", _id: ObjectId('69f1ca4339607e6b0844ba89') } ], ordered: true, lsid: { id: UUID("95eef997-5e58-4dea-8013-c7eaf1a29991") }, $db: "healthcare_db" }
```

**Résultat :** Erreur `not authorized` — l'écriture est bien bloquée pour le rôle `read`.

---

## Conclusion

Les 4 tests démontrent que :
- L'authentification MongoDB est active (test 2).
- Les comptes applicatifs sont créés automatiquement à l'init du conteneur (test 1).
- Le compte `migration_user` a les droits nécessaires pour la migration (test 3).
- Le compte `analyst_user` est strictement limité à la lecture, conformément au principe du moindre privilège (test 4b).

En cas de fuite des credentials de l'analyste, l'intégrité des données reste protégée.