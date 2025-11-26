#!/usr/bin/env python3
"""
ANALYZE DATABASE CAPTURES
Purpose: Check what fields are being populated vs empty in optimized schema tables
Identifies data gaps and capture issues
"""
import sqlite3
import json
from pathlib import Path

# Database path
db_path = Path(__file__).parent.parent / "chroma_db" / "rag.db"

def analyze_table(cursor, table_name: str) -> dict:
    """Analyze what's actually being captured in a table"""
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cursor.fetchone()[0]
    
    # Analyze each column
    analysis = {
        "table": table_name,
        "total_rows": total_rows,
        "columns": col_names,
        "data_quality": {}
    }
    
    for col_name in col_names:
        # Check nulls
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
        null_count = cursor.fetchone()[0]
        
        # Check empty strings
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} = ''")
        empty_count = cursor.fetchone()[0]
        
        # Get sample value
        cursor.execute(f"SELECT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL AND {col_name} != '' LIMIT 1")
        sample = cursor.fetchone()
        sample_value = sample[0] if sample else None
        
        # Summary
        populated = total_rows - null_count - empty_count if total_rows > 0 else 0
        populated_pct = (populated / total_rows * 100) if total_rows > 0 else 0
        
        analysis["data_quality"][col_name] = {
            "total": total_rows,
            "populated": populated,
            "null": null_count,
            "empty": empty_count,
            "percentage": round(populated_pct, 1),
            "sample": str(sample_value)[:100] if sample_value else None
        }
    
    return analysis

def analyze_json_column(cursor, table_name: str, col_name: str) -> dict:
    """Analyze JSON columns to see what fields are inside"""
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NOT NULL")
    total_with_json = cursor.fetchone()[0]
    
    if total_with_json == 0:
        return {"status": "empty"}
    
    # Get sample JSON
    cursor.execute(f"SELECT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 1")
    sample_row = cursor.fetchone()
    
    if sample_row and sample_row[0]:
        try:
            sample_json = json.loads(sample_row[0])
            keys = list(sample_json.keys())
            
            # Count which fields have values
            field_analysis = {}
            for key in keys:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table_name}
                    WHERE json_extract({col_name}, '$.{key}') IS NOT NULL
                """)
                populated = cursor.fetchone()[0]
                field_analysis[key] = {
                    "populated": populated,
                    "percentage": round(populated / total_with_json * 100, 1)
                }
            
            return {
                "status": "populated",
                "total_records_with_json": total_with_json,
                "fields_in_json": keys,
                "field_analysis": field_analysis,
                "sample": sample_json
            }
        except json.JSONDecodeError:
            return {"status": "invalid_json", "sample": str(sample_row[0])[:200]}
    
    return {"status": "empty"}

def main():
    """Run analysis"""
    
    if not db_path.exists():
        print(f"[!] Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*100)
    print("[*] DATABASE CAPTURE ANALYSIS: What's Being Stored vs What's Missing")
    print("="*100)
    
    tables_to_analyze = [
        'document_metadata',
        'chunk_embedding_data',
        'rag_history_and_optimization'
    ]
    
    all_analysis = {}
    
    for table_name in tables_to_analyze:
        print(f"\n\n{'='*100}")
        print(f"[TABLE] {table_name.upper()}")
        print(f"{'='*100}")
        
        analysis = analyze_table(cursor, table_name)
        all_analysis[table_name] = analysis
        
        print(f"[+] Total Rows: {analysis['total_rows']}")
        print(f"[+] Total Columns: {len(analysis['columns'])}")
        
        # Show data quality
        print(f"\n[FIELD CAPTURE ANALYSIS]")
        print(f"{'Field':<40} {'Populated':<12} {'Null':<10} {'Empty':<10} {'Pct':<8}")
        print("-" * 100)
        
        for col_name, quality in analysis["data_quality"].items():
            status = "[V]" if quality['percentage'] == 100 else "[~]" if quality['percentage'] > 0 else "[X]"
            print(f"{status} {col_name:<37} {quality['populated']:<12} {quality['null']:<10} {quality['empty']:<10} {quality['percentage']:<8}")
        
        # Check JSON columns
        json_columns = {
            'document_metadata': ['metadata_json'],
            'chunk_embedding_data': ['healing_suggestions'],
            'rag_history_and_optimization': ['metrics_json', 'context_json']
        }
        
        if table_name in json_columns:
            print(f"\n[JSON FIELD ANALYSIS]")
            for json_col in json_columns[table_name]:
                json_analysis = analyze_json_column(cursor, table_name, json_col)
                
                if json_analysis['status'] == 'populated':
                    print(f"\n  {json_col}:")
                    print(f"    Records with JSON: {json_analysis['total_records_with_json']}")
                    print(f"    Fields inside: {json_analysis['fields_in_json']}")
                    
                    print(f"\n    Field Capture Breakdown:")
                    for field, stats in json_analysis['field_analysis'].items():
                        status = "[V]" if stats['percentage'] == 100 else "[~]" if stats['percentage'] > 0 else "[X]"
                        print(f"      {status} {field:<40} {stats['percentage']:.1f}% populated")
                    
                    if json_analysis['sample']:
                        print(f"\n    Sample JSON:")
                        for k, v in json_analysis['sample'].items():
                            print(f"      - {k}: {str(v)[:50]}")
                else:
                    print(f"\n  {json_col}: {json_analysis['status'].upper()}")
    
    # Summary
    print(f"\n\n{'='*100}")
    print("[SUMMARY]")
    print(f"{'='*100}")
    
    for table_name, analysis in all_analysis.items():
        print(f"\n[Table] {table_name}:")
        
        unpopulated = []
        partial = []
        fully_populated = []
        
        for col_name, quality in analysis["data_quality"].items():
            if quality['percentage'] == 0:
                unpopulated.append(col_name)
            elif quality['percentage'] < 100:
                partial.append((col_name, quality['percentage']))
            else:
                fully_populated.append(col_name)
        
        if unpopulated:
            print(f"  [X] NEVER CAPTURED (0%): {', '.join(unpopulated)}")
        
        if partial:
            print(f"  [~] PARTIALLY CAPTURED:")
            for col, pct in partial:
                print(f"     - {col}: {pct}%")
        
        if fully_populated:
            print(f"  [V] FULLY CAPTURED: {len(fully_populated)} fields")
    
    conn.close()
    print(f"\n{'='*100}")
    print("[DONE] Analysis Complete")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    main()
