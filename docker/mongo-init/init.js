db = db.getSiblingDB("healthcare_db");

db.createUser({
  user: "etl_writer",
  pwd: "etl_writer_pwd",
  roles: [
    { role: "readWrite", db: "healthcare_db" }
  ]
});