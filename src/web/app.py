import os
import sqlite3
import json
import re
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="CurationInsight - Art Exhibition Intelligence Dashboard",
    description="Interactive data visualization platform for global contemporary art exhibitions",
    version="1.0.0"
)

# Enable CORS for local testing and developer integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "exhibitions.db"

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Helper to clean and extract 4-digit year from date string
def extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(date_str))
    return int(match.group(1)) if match else None

@app.get("/api/stats")
def get_stats():
    """Returns general database analytics and counts."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database file exhibitions.db not found.")
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # 1. Basic counts
        cursor.execute("SELECT COUNT(*) FROM exhibitions")
        total_exhibitions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM artworks")
        total_artworks = cursor.fetchone()[0]
        
        # 2. Institution distribution
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM exhibitions 
            GROUP BY source 
            ORDER BY count DESC
        """)
        museum_stats = [dict(row) for row in cursor.fetchall()]
        
        # 3. Top artists (excluding unknowns/group shows placeholders)
        cursor.execute("""
            SELECT artist_name, COUNT(*) as count 
            FROM artworks 
            WHERE artist_name != "" 
              AND artist_name NOT LIKE '%Various%' 
              AND artist_name NOT LIKE '%Unknown%' 
              AND artist_name NOT LIKE '%[Various]%'
              AND artist_name NOT LIKE '%Multiple%'
            GROUP BY artist_name 
            ORDER BY count DESC 
            LIMIT 15
        """)
        top_artists = [dict(row) for row in cursor.fetchall()]
        
        # 4. Mediums distribution (with some simple grouping)
        cursor.execute("""
            SELECT medium, COUNT(*) as count 
            FROM artworks 
            WHERE medium != "" 
              AND medium IS NOT NULL
            GROUP BY medium 
            ORDER BY count DESC 
            LIMIT 12
        """)
        medium_stats = [dict(row) for row in cursor.fetchall()]
        
        # 5. Cities distribution
        cursor.execute("""
            SELECT city, COUNT(*) as count 
            FROM exhibitions 
            WHERE city != "" AND city IS NOT NULL
            GROUP BY city 
            ORDER BY count DESC
        """)
        city_stats = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_exhibitions": total_exhibitions,
            "total_artworks": total_artworks,
            "museum_stats": museum_stats,
            "top_artists": top_artists,
            "medium_stats": medium_stats,
            "city_stats": city_stats
        }
    finally:
        conn.close()

@app.get("/api/timeline")
def get_timeline():
    """Returns chronologically ordered statistics grouped by year and museum for Stream/River layout."""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Get all exhibitions and their start_date
        cursor.execute("SELECT id, source, start_date FROM exhibitions WHERE start_date != '' AND start_date IS NOT NULL")
        rows = cursor.fetchall()
        
        # Aggregate in Python for robust year extraction
        yearly_data = {} # {year: {source: count}}
        all_sources = set()
        
        for row in rows:
            source = row["source"]
            all_sources.add(source)
            year = extract_year(row["start_date"])
            if year:
                # Limit to reasonable contemporary history range
                if 1920 <= year <= 2026:
                    if year not in yearly_data:
                        yearly_data[year] = {}
                    yearly_data[year][source] = yearly_data[year].get(source, 0) + 1
                    
        # Sort years
        sorted_years = sorted(list(yearly_data.keys()))
        sources_list = sorted(list(all_sources))
        
        series_data = {src: [] for src in sources_list}
        for yr in sorted_years:
            for src in sources_list:
                series_data[src].append(yearly_data[yr].get(src, 0))
                
        return {
            "years": sorted_years,
            "museums": sources_list,
            "series": series_data
        }
    finally:
        conn.close()

@app.get("/api/network")
def get_network(limit_artists: int = 100, min_cooccurrence: int = 2):
    """Calculates top artists co-occurrence network schema for force-directed graphs."""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # 1. Identify top active artists in exhibitions
        cursor.execute("""
            SELECT artist_name, COUNT(*) as count 
            FROM artworks 
            WHERE artist_name != "" 
              AND artist_name NOT LIKE '%Various%' 
              AND artist_name NOT LIKE '%Unknown%' 
              AND artist_name NOT LIKE '%[Various]%'
              AND artist_name NOT LIKE '%Multiple%'
            GROUP BY artist_name 
            ORDER BY count DESC 
            LIMIT ?
        """, (limit_artists,))
        
        top_artists_rows = cursor.fetchall()
        top_artists = {row["artist_name"]: row["count"] for row in top_artists_rows}
        artists_names = list(top_artists.keys())
        
        if not artists_names:
            return {"nodes": [], "links": []}
            
        # Build SQL placeholders
        placeholders = ",".join(["?"] * len(artists_names))
        
        # 2. Query co-occurrence relations using self join
        sql = f"""
            SELECT a1.artist_name as source, a2.artist_name as target, COUNT(*) as weight
            FROM artworks a1
            JOIN artworks a2 ON a1.exhibition_id = a2.exhibition_id
            WHERE a1.artist_name IN ({placeholders})
              AND a2.artist_name IN ({placeholders})
              AND a1.artist_name < a2.artist_name
            GROUP BY a1.artist_name, a2.artist_name
            HAVING weight >= ?
            ORDER BY weight DESC
            LIMIT 300
        """
        
        query_params = artists_names + artists_names + [min_cooccurrence]
        cursor.execute(sql, query_params)
        links_rows = cursor.fetchall()
        
        # 3. Build Nodes and Links
        # Keep only nodes that have at least one link to prevent floating isolated dots (which look cluttered)
        connected_artists = set()
        links = []
        for row in links_rows:
            connected_artists.add(row["source"])
            connected_artists.add(row["target"])
            links.append({
                "source": row["source"],
                "target": row["target"],
                "value": row["weight"]
            })
            
        nodes = []
        for name in connected_artists:
            nodes.append({
                "id": name,
                "name": name,
                "value": top_artists.get(name, 1),
                "symbolSize": max(6, min(22, 6 + (top_artists.get(name, 1) ** 0.5) * 1.0)) # Flat square root model to prevent huge bubbles
            })

            
        return {
            "nodes": nodes,
            "links": links
        }
    finally:
        conn.close()

@app.get("/api/exhibitions")
def get_exhibitions(
    source: Optional[str] = None,
    query: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 20,
    offset: int = 0
):
    """Retrieves list of exhibitions with advanced pagination and keyword filtering."""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        where_clauses = ["1=1"]
        params = []
        
        if source:
            where_clauses.append("source = ?")
            params.append(source)
            
        if start_year:
            # Simple matching on start_date containing or being >= start_year
            where_clauses.append("CAST(SUBSTR(start_date, 1, 4) AS INTEGER) >= ?")
            params.append(start_year)
            
        if end_year:
            where_clauses.append("CAST(SUBSTR(start_date, 1, 4) AS INTEGER) <= ?")
            params.append(end_year)
            
        if query:
            # Dynamic multi-field search (title, curators, location, preface, concept, preface_en, concept_en, or search on artist names in artworks)
            subquery = """
                id IN (
                    SELECT id FROM exhibitions 
                    WHERE title LIKE ? OR preface LIKE ? OR concept LIKE ? OR curators LIKE ? OR location LIKE ? OR preface_en LIKE ? OR concept_en LIKE ?
                    UNION
                    SELECT exhibition_id FROM artworks 
                    WHERE artist_name LIKE ? OR work_title LIKE ?
                )
            """
            where_clauses.append(subquery)
            like_query = f"%{query}%"
            params.extend([like_query] * 9)
            
        where_str = " AND ".join(where_clauses)
        
        # 1. Total matching count
        cursor.execute(f"SELECT COUNT(*) FROM exhibitions WHERE {where_str}", params)
        total_count = cursor.fetchone()[0]
        
        # 2. Main data query
        sql = f"""
            SELECT id, source, title, curators, start_date, end_date, location, city, url, tags
            FROM exhibitions 
            WHERE {where_str} 
            ORDER BY start_date DESC, id DESC 
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, params + [limit, offset])
        rows = cursor.fetchall()
        
        exhibitions = []
        for row in rows:
            ex_data = dict(row)
            try:
                ex_data["curators"] = json.loads(ex_data["curators"]) if ex_data.get("curators") else []
            except json.JSONDecodeError:
                ex_data["curators"] = [ex_data["curators"]] if ex_data.get("curators") else []
            
            try:
                ex_data["tags"] = json.loads(ex_data["tags"]) if ex_data.get("tags") else []
            except json.JSONDecodeError:
                ex_data["tags"] = []
                
            # Subquery artwork count for dashboard grid preview
            cursor.execute("SELECT COUNT(*) FROM artworks WHERE exhibition_id = ?", (ex_data["id"],))
            ex_data["artwork_count"] = cursor.fetchone()[0]
            exhibitions.append(ex_data)
            
        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "data": exhibitions
        }
    finally:
        conn.close()

@app.get("/api/exhibitions/{exhibition_id}")
def get_exhibition_details(exhibition_id: int):
    """Retrieves full exhibition details, curatorial concept text, and complete list of artworks."""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM exhibitions WHERE id = ?", (exhibition_id,))
        ex_row = cursor.fetchone()
        if not ex_row:
            raise HTTPException(status_code=404, detail="Exhibition not found")
            
        ex_data = dict(ex_row)
        try:
            ex_data["curators"] = json.loads(ex_data["curators"]) if ex_data.get("curators") else []
        except json.JSONDecodeError:
            ex_data["curators"] = [ex_data["curators"]] if ex_data.get("curators") else []
            
        try:
            ex_data["tags"] = json.loads(ex_data["tags"]) if ex_data.get("tags") else []
        except json.JSONDecodeError:
            ex_data["tags"] = []
            
        # Get all artworks
        cursor.execute("""
            SELECT id, artist_name, work_title, work_year, medium, dimensions, caption 
            FROM artworks 
            WHERE exhibition_id = ?
            ORDER BY artist_name ASC, work_title ASC
        """, (exhibition_id,))
        art_rows = cursor.fetchall()
        ex_data["artworks"] = [dict(row) for row in art_rows]
        
        return ex_data
    finally:
        conn.close()

# serve root files
@app.get("/", response_class=HTMLResponse)
def get_index():
    index_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>CurationInsight Dashboard</h1><p>Index file templates/index.html not found.</p>")

@app.get("/favicon.ico", include_in_schema=False)
def get_favicon():
    return Response(content=b"", media_type="image/x-icon")

# Mount static and templates folders properly
# Since static dir might contain JS/CSS, let's mount it safely if it exists
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path, exist_ok=True)
    
templates_path = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_path):
    os.makedirs(templates_path, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_path), name="static")
