#!/usr/bin/env python3
"""
ANALYZE DATABASE CAPTURES
Purpose: Check what fields are being populated vs empty in optimized schema tables
Identifies data gaps and capture issues
"""
import sqlite3
import json
from pathlib import Path
from collections import defaultdict

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
    
    print("\n" + "="*90)
    print("[*] DATABASE CAPTURE ANALYSIS: What's Being Stored vs What's Missing")
    print("="*90)
    
    tables_to_analyze = [
        'document_metadata',
        'chunk_embedding_data',
        'rag_history_and_optimization'
    ]
    
    all_analysis = {}
    
    for table_name in tables_to_analyze:
        print(f"\n\n{'='*90}")
        print(f"📋 TABLE: {table_name.upper()}")
        print(f"{'='*90}")
        
        analysis = analyze_table(cursor, table_name)
        all_analysis[table_name] = analysis
        
        print(f"✓ Total Rows: {analysis['total_rows']}")
        print(f"✓ Total Columns: {len(analysis['columns'])}")
        
        # Show data quality
        print(f"\n📊 FIELD CAPTURE ANALYSIS:")
        print(f"{'Field':<40} {'Populated':<15} {'Null':<10} {'Empty':<10} {'%':<8} {'Sample':<20}")
        print("-" * 120)
        
        for col_name, quality in analysis["data_quality"].items():
            sample_str = str(quality['sample'])[:20] if quality['sample'] else "NULL"
            status = "✓" if quality['percentage'] == 100 else "⚠" if quality['percentage'] > 0 else "✗"
            
            print(f"{status} {col_name:<38} {quality['populated']:<15} {quality['null']:<10} {quality['empty']:<10} {quality['percentage']:<8} {sample_str:<20}")
        
        # Check JSON columns
        json_columns = {
            'document_metadata': ['metadata_json'],
            'chunk_embedding_data': ['healing_suggestions'],
            'rag_history_and_optimization': ['metrics_json', 'context_json']
        }
        
        if table_name in json_columns:
            print(f"\n📄 JSON FIELD ANALYSIS:")
            for json_col in json_columns[table_name]:
                json_analysis = analyze_json_column(cursor, table_name, json_col)
                
                if json_analysis['status'] == 'populated':
                    print(f"\n  {json_col}:")
                    print(f"    Records with JSON: {json_analysis['total_records_with_json']}")
                    print(f"    Fields inside: {json_analysis['fields_in_json']}")
                    
                    print(f"\n    Field Capture Breakdown:")
                    for field, stats in json_analysis['field_analysis'].items():
                        status = "✓" if stats['percentage'] == 100 else "⚠" if stats['percentage'] > 0 else "✗"
                        print(f"      {status} {field:<40} {stats['percentage']:.1f}% populated")
                    
                    print(f"\n    Sample JSON:")
                    print(f"    {json.dumps(json_analysis['sample'], indent=6)}")
                else:
                    print(f"\n  {json_col}: {json_analysis['status'].upper()}")
    
    # Summary and recommendations
    print(f"\n\n{'='*90}")
    print("🎯 SUMMARY & RECOMMENDATIONS")
    print(f"{'='*90}")
    
    for table_name, analysis in all_analysis.items():
        print(f"\n📌 {table_name}:")
        
        # Find unpopulated fields
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
            print(f"  ❌ NEVER CAPTURED (0%): {', '.join(unpopulated)}")
        
        if partial:
            print(f"  ⚠️  PARTIALLY CAPTURED:")
            for col, pct in partial:
                print(f"     - {col}: {pct}%")
        
        if fully_populated:
            print(f"  ✓ FULLY CAPTURED: {len(fully_populated)} fields")
    
    # Gap analysis
    print(f"\n\n{'='*90}")
    print("🔍 DATA GAP ANALYSIS: What Should We Be Capturing?")
    print(f"{'='*90}")
    
    gaps = {
        'document_metadata': [
            ('metadata_json', 'Document tags, classifications, processing flags'),
            ('summary', 'Document summary/abstract'),
            ('author', 'Document author information')
        ],
        'chunk_embedding_data': [
            ('healing_suggestions', 'AI-generated suggestions for improving chunk'),
            ('quality_score', 'Automated quality metric (0-1)'),
            ('reindex_count', 'How many times this chunk has been re-indexed')
        ],
        'rag_history_and_optimization': [
            ('metrics_json.user_feedback', 'User satisfaction score'),
            ('metrics_json.cost_tokens', 'Token cost for the operation'),
            ('context_json.reasoning', 'Why this action was taken'),
            ('reward_signal', 'RL agent reward value'),
            ('action_taken', 'Which healing action was applied')
        ]
    }
    
    for table_name, gap_fields in gaps.items():
        print(f"\n📌 {table_name}:")
        for field, purpose in gap_fields:
            actual = analysis.get("data_quality", {}).get(field, {}).get("percentage", "?")
            if actual == 0 or actual == "?":
                print(f"  ❌ {field}: {purpose}")
            else:
                print(f"  ✓ {field}: {purpose} ({actual}% captured)")
    
    conn.close()
    
    print(f"\n\n{'='*90}")
    print("✅ Analysis Complete")
    print(f"{'='*90}\n")

if __name__ == "__main__":
    main()
