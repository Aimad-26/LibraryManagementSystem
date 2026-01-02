import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Vérifiez d'abord quelles colonnes existent
cursor.execute("PRAGMA table_info(client_app_loan)")
existing_columns = [column[1] for column in cursor.fetchall()]
print("Colonnes existantes:", existing_columns)

# Ajoutez due_date si elle n'existe pas
if 'due_date' not in existing_columns:
    try:
        cursor.execute("ALTER TABLE client_app_loan ADD COLUMN due_date DATE")
        print("✓ Colonne 'due_date' ajoutée")
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"❌ Erreur due_date: {e}")
else:
    print("⚠ Colonne 'due_date' existe déjà")

# Ajoutez return_date si elle n'existe pas
if 'return_date' not in existing_columns:
    try:
        cursor.execute("ALTER TABLE client_app_loan ADD COLUMN return_date DATE")
        print("✓ Colonne 'return_date' ajoutée")
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"❌ Erreur return_date: {e}")
else:
    print("⚠ Colonne 'return_date' existe déjà")

conn.close()
print("\n✅ Terminé! Redémarrez le serveur.")