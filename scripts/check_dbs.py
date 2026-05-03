import sqlite3, os
for db in ['jarvis_dev.db','jarvis_events.db']:
    path = os.path.join(os.getcwd(), db)
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(db, 'tables:', tables)
        for t in ['events','patterns','interventions']:
            if t in tables:
                try:
                    cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    print(' ', t, cnt)
                except Exception as e:
                    print(' ', t, 'error', e)
        conn.close()
    else:
        print(db, 'not found')
