#!/usr/bin/env python3
import os
import subprocess
import sys
import time


def test_imports():
    """Test the imports that GitHub Actions is trying to use"""
    try:
        # Change to backend directory
        os.chdir("/Users/eli/github/tunemeld/backend")

        # Test the problematic import
        result = subprocess.run(
            [
                "python",
                "manage.py",
                "shell",
                "-c",
                """
import sys
sys.path.insert(0, '/Users/eli/github/tunemeld')
from core.management.commands.view_count_modules.c_clear_view_count_cache import Command as ClearViewCountCacheCommand
from core.utils.local_cache import local_cache_clear, CachePrefix
print("✅ All imports successful!")
print("Available cache prefixes:", [p.value for p in CachePrefix])
""",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ SUCCESS: All imports working correctly!")
            print("STDOUT:", result.stdout.strip())
            return True
        else:
            print("❌ FAILED: Import error")
            print("STDOUT:", result.stdout.strip())
            print("STDERR:", result.stderr.strip())
            return False

    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Command took too long")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False


def main():
    print("🔄 Starting continuous GitHub Actions import testing...")
    print("Will test every 10 seconds until successful or 10 attempts")

    for attempt in range(1, 11):
        print(f"\n--- Attempt {attempt}/10 ---")

        if test_imports():
            print(f"🎉 SUCCESS after {attempt} attempts!")
            break

        if attempt < 10:
            print("😴 Sleeping 10 seconds before retry...")
            time.sleep(10)
    else:
        print("💀 FAILED after 10 attempts")
        sys.exit(1)


if __name__ == "__main__":
    main()
