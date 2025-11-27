# Hardcoded Database Paths - Complete List

**Files Still Using Hardcoded `chroma_db` and `rag.db` Paths**

---

## 1. Database Models (3 files)

### `src/incident_iq/database/models/rag_history_model.py`
**Location:** Line 27  
**Current Code:**
```python
def __init__(self, db_path: str = None):
    if db_path is None:
        # Use optimized schema path: chroma_db/rag.db
        # File is at: src/incident_iq/database/models/rag_history_model.py
        # Go up 5 levels: models → database → incident_iq → src → PROJECT_ROOT
        project_root = Path(__file__).parent.parent.parent.parent.parent
        db_path = str(project_root / "chroma_db" / "rag.db")
```

**Issue:** Hardcoded path construction, should use `EnvConfig`

---

### `src/incident_iq/database/models/chunk_embedding_data_model.py`
**Location:** Line 32  
**Current Code:**
```python
def __init__(self, db_path: str = None):
    if db_path is None:
        # Use config-based path: chroma_db/rag.db
        try:
            from ..config import get_database_dir, get_database_name
            db_dir_name = get_database_dir()
            db_name = get_database_name()
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / db_dir_name / db_name)
        except Exception:
            # Fallback to default chroma_db/rag.db
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / "chroma_db" / "rag.db")
```

**Issue:** Fallback hardcodes path, and tries to import from local config instead of `EnvConfig`

---

### `src/incident_iq/database/models/document_metadata_model.py`
**Location:** Line 32  
**Current Code:**
```python
def __init__(self, db_path: str = None):
    if db_path is None:
        # Use config-based path: chroma_db/rag.db
        try:
            from ..config import get_database_dir, get_database_name
            db_dir_name = get_database_dir()
            db_name = get_database_name()
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / db_dir_name / db_name)
        except Exception:
            # Fallback to default chroma_db/rag.db
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = str(project_root / "chroma_db" / "rag.db")
```

**Issue:** Same as above - fallback hardcodes path, local config import instead of `EnvConfig`

---

## 2. Healing Agent (1 file)

### `src/incident_iq/rag/agents/healing_agent/rl_healing_agent.py`
**Location:** Line 428 (in `example_usage()` function)  
**Current Code:**
```python
def example_usage():
    """Example of how to use the RL Healing Agent"""
    
    # Initialize agent
    db_path = "./chroma_db/rag.db"  # ← HARDCODED
    agent = RLHealingAgent(db_path)
```

**Issue:** Hardcoded path in example/test code - should use `EnvConfig.get_db_path()`

---

## 3. Migration Scripts (3 files)

### `src/incident_iq/database/migration/optimized_schema/run_migration.py`
**Location:** Line 200  
**Current Code:**
```python
def main():
    # Default paths
    db_path = os.getenv(
        "CHROMA_DB_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "chroma_db", "rag.db")
    )
```

**Issue:** Mixes `os.getenv()` with hardcoded path construction instead of using `EnvConfig`

---

### `scripts/run_migration_wrapper.py`
**Location:** Line 42 (in `get_default_db_path()` function)  
**Current Code:**
```python
def get_default_db_path() -> Path:
    """Get default database path"""
    # Try to get from config
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from incident_iq.config import get_database_dir, get_database_name
        db_dir_name = get_database_dir()
        db_name = get_database_name()
        db_path = Path(__file__).parent.parent / db_dir_name / db_name
        return db_path
    except Exception:
        # Fallback to default
        return Path(__file__).parent.parent / "chroma_db" / "rag.db"  # ← HARDCODED
```

**Issue:** Fallback hardcodes path, should use `EnvConfig`

---

### `scripts/run_optimized_migration.py`
**Location:** Line 20  
**Current Code:**
```python
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    db_path = project_root / "chroma_db" / "rag.db"  # ← HARDCODED
```

**Issue:** Direct hardcoded path construction - should use `EnvConfig.get_db_path()`

---

## 4. Test Files

✅ **DELETED** - All 4 test files removed:
- `test_deepagents_healing_fixed.py`
- `test_deepagents_healing.py`
- `test_deepagents_enhanced.py`
- `test_deepagents_comprehensive.py`

---

## 5. Configuration File (1 file)

### `src/incident_iq/config.py`
**Location:** Line 96  
**Current Code:**
```python
def get_vector_db_dir():
    return get_config().get('vector-db-dir', 'data/chroma_db')  # ← DIFFERENT PATH!
```

**Issue:** Uses different fallback path (`data/chroma_db` instead of `chroma_db`) - inconsistent with other parts

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Database Models | 3 | ⚠️ Using local config imports + hardcoded fallbacks |
| Healing Agent | 1 | ⚠️ Example code with hardcoded path |
| Migration Scripts | 3 | ⚠️ Mix of os.getenv() and hardcoded fallbacks |
| Test Files | 0 | ✅ **DELETED** |
| Config Files | 1 | ⚠️ Different fallback path (data/chroma_db) |
| **TOTAL** | **8** | **Remaining files to update** |

---

## EnvConfig Methods Already Available

```python
# From src/incident_iq/rag/config/env_config.py
EnvConfig.get_db_path()           # → 'chroma_db/rag.db'
EnvConfig.get_chroma_db_path()    # → 'chroma_db'
EnvConfig.get_rag_config_path()   # → 'src/incident_iq/rag/config'
EnvConfig.get_app_env()           # → 'development' or from $APP_ENV
EnvConfig.get_log_level()         # → 'info' or from $LOG_LEVEL
```

---

## Recommended Actions

1. **Update all 3 database models** to use `EnvConfig.get_db_path()` instead of path construction
2. **Update RL healing agent example** to use `EnvConfig.get_db_path()`
3. **Update migration scripts** to use `EnvConfig` for consistency
4. **Update all 4 test files** to use `EnvConfig.get_db_path()`
5. **Fix `src/incident_iq/config.py`** to align fallback path or use `EnvConfig`

---

## Priority Order (Recommended)

### 🔴 HIGH PRIORITY
- Database models (3 files) - These are core infrastructure
- Migration scripts (3 files) - Database setup must be consistent

### 🟡 MEDIUM PRIORITY  
- Healing agent example (1 file) - Example code clarity

### 🟢 LOW PRIORITY
- Config file (1 file) - Minor fallback inconsistency

---

## Notes

- **RL Healing Agent** doesn't have hardcoded path in the main class - only in example usage
- **Database Models** were trying to use local config but should centralize on `EnvConfig`
- **Migration Scripts** need refactoring to avoid path construction duplication
- **Test Files** can be easily updated for consistency
- **Config File** has a different fallback path that may indicate legacy code

