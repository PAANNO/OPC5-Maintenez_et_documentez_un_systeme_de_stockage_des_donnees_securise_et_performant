/**
 * Initialisation des utilisateurs applicatifs.
 *
 * Ce script s'exécute UNE SEULE FOIS au tout premier démarrage du conteneur
 * (quand /data/db est vide). Pour le re-jouer, il faut supprimer le volume :
 *   docker compose down -v
 *
 * L'utilisateur root (admin) est déjà créé par MongoDB via les variables
 * d'environnement MONGO_INITDB_ROOT_USERNAME / MONGO_INITDB_ROOT_PASSWORD.
 *
 * Les mots de passe des autres utilisateurs sont injectés via variables
 * d'environnement (cf. docker-compose.yml).
 *
 * Stratégie de rôles (principe du moindre privilège) :
 *   - admin             : root, gestion des utilisateurs, opérations DBA
 *   - migration_user    : readWrite sur healthcare_db (utilisé par le migrator)
 *   - analyst_user      : read sur healthcare_db (lecture seule pour reporting)
 */

const migrationPassword = process.env.MIGRATION_USER_PASSWORD;
const analystPassword = process.env.ANALYST_USER_PASSWORD;

if (!migrationPassword || !analystPassword) {
  throw new Error(
    "Variables MIGRATION_USER_PASSWORD et ANALYST_USER_PASSWORD requises dans l'environnement."
  );
}

// On crée les utilisateurs applicatifs sur la base healthcare_db
db = db.getSiblingDB("healthcare_db");

db.createUser({
  user: "migration_user",
  pwd: migrationPassword,
  roles: [{ role: "readWrite", db: "healthcare_db" }],
});
print("Utilisateur 'migration_user' créé (readWrite sur healthcare_db)");

db.createUser({
  user: "analyst_user",
  pwd: analystPassword,
  roles: [{ role: "read", db: "healthcare_db" }],
});
print("Utilisateur 'analyst_user' créé (read sur healthcare_db)");

print("Initialisation des utilisateurs terminée.");