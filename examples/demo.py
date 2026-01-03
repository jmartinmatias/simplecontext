"""
SimpleContext Demo
Shows the 6 core operations in action.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory import SimpleMemory
import tempfile

def main():
    # Create temporary database for demo
    temp_db = tempfile.mktemp(suffix='.db')
    print(f"Demo database: {temp_db}\n")

    mem = SimpleMemory(temp_db)

    print("=" * 60)
    print("SimpleContext Demo: 6 Core Operations")
    print("=" * 60)

    # 1. Remember
    print("\n1. REMEMBER - Store a memory")
    print("-" * 60)
    mem_id = mem.remember("Using PostgreSQL 14 on port 5432", tags=["database", "config"])
    mem.remember("API key is in .env file", tags=["security", "config"])
    mem.remember("Deploy to staging before production", tags=["deployment", "process"])

    # 2. Recall
    print("\n2. RECALL - Search memories")
    print("-" * 60)
    print("\nSearching for 'database':")
    results = mem.recall("database")
    for r in results:
        print(f"  - {r['content']}")
        print(f"    Tags: {r['tags']}, Age: {r['age_days']:.1f} days")

    # 3. Store
    print("\n3. STORE - Save large artifact")
    print("-" * 60)
    code = """
def connect_to_db():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='myapp',
        user='postgres'
    )
"""
    mem.store("db_config.py", code)

    # 4. Retrieve
    print("\n4. RETRIEVE - Get artifact back")
    print("-" * 60)
    retrieved = mem.retrieve("db_config.py")
    print(f"Retrieved artifact:\n{retrieved}")

    # 5. Status
    print("\n5. STATUS - Check what's stored")
    print("-" * 60)
    status = mem.status()
    print(f"Memories: {status['memories']}")
    print(f"Artifacts: {status['artifacts']}")
    print(f"Mode: {status['mode']}")

    # 6. Forget
    print("\n6. FORGET - Delete a memory")
    print("-" * 60)
    count = mem.forget("API key")
    print(f"Forgot {count} memories")

    # Final status
    print("\n" + "=" * 60)
    print("Final Status")
    print("=" * 60)
    status = mem.status()
    print(f"Memories: {status['memories']}")
    print(f"Artifacts: {status['artifacts']}")

    print(f"\n✅ Demo complete! Database saved at: {temp_db}")
    print("You can inspect it with: sqlite3", temp_db)

if __name__ == "__main__":
    main()
