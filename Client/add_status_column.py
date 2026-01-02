import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    # Ajoutez la colonne status
    cursor.execute("ALTER TABLE client_app_loan ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE'")
    print("✓ Colonne 'status' ajoutée")
except sqlite3.OperationalError as e:
    print(f"Colonne 'status': {e}")

try:
    # Ajoutez la colonne loan_date
    cursor.execute("ALTER TABLE client_app_loan ADD COLUMN loan_date DATETIME")
    print("✓ Colonne 'loan_date' ajoutée")
except sqlite3.OperationalError as e:
    print(f"Colonne 'loan_date': {e}")

try:
    # Ajoutez la colonne due_date
    cursor.execute("ALTER TABLE client_app_loan ADD COLUMN due_date DATE")
    print("✓ Colonne 'due_date' ajoutée")
except sqlite3.OperationalError as e:
    print(f"Colonne 'due_date': {e}")

try:
    # Ajoutez la colonne return_date
    cursor.execute("ALTER TABLE client_app_loan ADD COLUMN return_date DATE")
    print("✓ Colonne 'return_date' ajoutée")
except sqlite3.OperationalError as e:
    print(f"Colonne 'return_date': {e}")

conn.commit()
conn.close()
print("\n✅ Modifications terminées! Redémarrez le serveur.")