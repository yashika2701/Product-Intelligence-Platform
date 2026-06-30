import sqlite3

def run_verification():
    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    
    with open("analytics_queries.sql", "r") as f:
        sql_content = f.read()
        
    # Split by semicolon to isolate individual query blocks
    raw_queries = sql_content.split(";")
    queries = []
    for q in raw_queries:
        cleaned = q.strip()
        if cleaned:
            queries.append(cleaned)
            
    query_names = [
        "1. FUNNEL ANALYSIS BY DEVICE TYPE",
        "2. COHORT RETENTION BY ACQUISITION CHANNEL",
        "3. TOP-LINE MARKETPLACE KPIs"
    ]
    
    for name, query in zip(query_names, queries):
        print("\n" + "="*60)
        print(f" QUERY BLOCK: {name}")
        print("="*60)
        try:
            cursor.execute(query)
            headers = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Format outputs as a text table
            # Compute max widths of columns
            col_widths = [len(h) for h in headers]
            for row in rows:
                for idx, val in enumerate(row):
                    col_widths[idx] = max(col_widths[idx], len(str(val)))
            
            # Print headers
            header_row = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
            print(header_row)
            print("-" * len(header_row))
            
            # Print rows
            for row in rows:
                print(" | ".join(f"{str(val):<{col_widths[i]}}" for i, val in enumerate(row)))
                
        except Exception as e:
            print(f"Error running query: {e}")
            # Print query segment for debugging if failed
            print("Query content:\n", query)
            
    conn.close()

if __name__ == "__main__":
    run_verification()
