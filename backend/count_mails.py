from database_mongo import get_db

db = get_db()
count = db.gmail_config.count_documents({})
print(f'Total Gmail configs in database: {count}')

configs = list(db.gmail_config.find({}))
print(f'Actually retrieved: {len(configs)}\n')

for i, c in enumerate(configs, 1):
    print(f'{i}. {c.get("email", "N/A")} (ID: {c["_id"]})')
