import sqlite3
import re

db_path = "exhibitions.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all Serpentine Galleries exhibitions
cursor.execute("SELECT id, title, url FROM exhibitions WHERE source = 'Serpentine Galleries'")
rows = cursor.fetchall()

print(f"Total Serpentine entries currently: {len(rows)}")

event_keywords = [
    r"talk", r"workshop", r"symposium", r"seminar", r"conference", r"lecture", r"conversation",
    r"screening", r"film", r"performance", r"concert", r"recital", r"study-evening", r"celebration",
    r"launch", r"reading", r"discussion", r"panel", r"gala", r"dinner", r"salon", r"tour", r"school-visit",
    r"podcast", r"marathon", r"park-nights", r"saturday-talks", r"book-club", r"study-day"
]

event_pattern = re.compile(
    r"\b(" + "|".join(event_keywords) + r")s?\b|(-talks|-nights|workshop|symposium|seminar|conference|lecture|conversation|screening|performance|concert|launch|reading|discussion|panel|tour|podcast|marathon)",
    re.IGNORECASE
)

to_delete_ids = []
to_delete_details = []

for row in rows:
    title = row["title"]
    url = row["url"]
    ex_id = row["id"]
    
    is_event_or_index = False
    
    # 1. Exclude if contains /archive/
    if "/archive/" in url:
        is_event_or_index = True
    # 2. Exclude by event keywords in URL or Title
    elif event_pattern.search(url) or event_pattern.search(title):
        is_event_or_index = True
        
    if is_event_or_index:
        to_delete_ids.append(ex_id)
        to_delete_details.append((ex_id, title, url))

print(f"\nFlagged {len(to_delete_ids)} entries for deletion.")

if to_delete_ids:
    print("\nStarting database cleanup...")
    
    # 1. Enable Foreign Key just in case
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # 2. Explicitly delete artworks to be 100% safe
    # Let's count how many artworks will be deleted
    placeholders = ",".join("?" for _ in to_delete_ids)
    cursor.execute(f"SELECT COUNT(*) as count FROM artworks WHERE exhibition_id IN ({placeholders})", to_delete_ids)
    artwork_del_count = cursor.fetchone()["count"]
    
    cursor.execute(f"DELETE FROM artworks WHERE exhibition_id IN ({placeholders})", to_delete_ids)
    print(f"  - Deleted {artwork_del_count} associated artworks from database.")
    
    # 3. Delete exhibitions
    cursor.execute(f"DELETE FROM exhibitions WHERE id IN ({placeholders})", to_delete_ids)
    print(f"  - Deleted {len(to_delete_ids)} exhibitions from database.")
    
    conn.commit()
    print("Database cleanup completed successfully.")
else:
    print("No entries flagged for deletion.")

# Print final Serpentine count
cursor.execute("SELECT COUNT(*) as count FROM exhibitions WHERE source = 'Serpentine Galleries'")
final_count = cursor.fetchone()["count"]
print(f"\nFinal Serpentine Galleries entries count in DB: {final_count}")

# Print total database stats
cursor.execute("SELECT COUNT(*) as count FROM exhibitions")
total_ex = cursor.fetchone()["count"]
cursor.execute("SELECT COUNT(*) as count FROM artworks")
total_art = cursor.fetchone()["count"]
print(f"Total database stats: Exhibitions={total_ex} | Artworks={total_art}")

conn.close()
