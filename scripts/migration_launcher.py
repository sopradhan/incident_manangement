#!/usr/bin/env python3
"""
Migration Launcher: Simple interface for running migrations
Provides multiple ways to run the optimized schema migration
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str = "") -> int:
    """Run a command and handle output"""
    print(f"\n{'='*70}")
    if description:
        print(f"📝 {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Show options and run selected migration"""
    script_dir = Path(__file__).parent
    
    print(f"\n{'='*70}")
    print("🗂️  Migration Options")
    print(f"{'='*70}")
    print("\n1. Run full migration (with table drop)")
    print("   Command: python scripts/run_migration_wrapper.py")
    print("\n2. Run migration (skip table drop - fresh DB)")
    print("   Command: python scripts/run_migration_wrapper.py --skip-drop")
    print("\n3. Verify schema only (no migration)")
    print("   Command: python scripts/run_migration_wrapper.py --verify-only")
    print("\n4. Verbose migration (detailed output)")
    print("   Command: python scripts/run_migration_wrapper.py --verbose")
    print("\n5. Custom database path")
    print("   Command: python scripts/run_migration_wrapper.py --db-path /path/to/db.db")
    print(f"\n{'='*70}\n")
    
    # Get user choice
    try:
        choice = input("Select option (1-5) or 'q' to quit: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 0
    
    if choice == 'q':
        print("Exiting...")
        return 0
    
    # Map choices to commands
    commands = {
        '1': (
            [sys.executable, str(script_dir / "run_migration_wrapper.py")],
            "Full migration with table drop"
        ),
        '2': (
            [sys.executable, str(script_dir / "run_migration_wrapper.py"), "--skip-drop"],
            "Migration without table drop"
        ),
        '3': (
            [sys.executable, str(script_dir / "run_migration_wrapper.py"), "--verify-only"],
            "Schema verification only"
        ),
        '4': (
            [sys.executable, str(script_dir / "run_migration_wrapper.py"), "--verbose"],
            "Verbose migration"
        ),
        '5': (
            [sys.executable, str(script_dir / "run_migration_wrapper.py"), "--db-path", 
             input("Enter database path: ").strip()],
            "Migration with custom database"
        ),
    }
    
    if choice not in commands:
        print("❌ Invalid choice")
        return 1
    
    cmd, desc = commands[choice]
    return run_command(cmd, desc)


if __name__ == "__main__":
    sys.exit(main())
