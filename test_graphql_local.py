#!/usr/bin/env python3
"""Local test for GraphQL query execution that mirrors Vercel serverless function behavior."""

import os
import sys
from pathlib import Path


def test_graphql_execution():
    """Test GraphQL query execution like in Vercel function."""
    print("Testing GraphQL execution locally...")

    try:
        # Setup Django (same as in Vercel function)
        backend_dir = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_dir))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

        import django

        django.setup()

        from core.graphql.schema import schema

        print("✓ Django and schema imported successfully")

        # Test a simple GraphQL query
        query = "{ __schema { types { name } } }"
        print(f"Executing query: {query}")

        result = schema.execute(query)
        print("✓ Query executed successfully")
        print(f"Data: {result.data is not None}")

        if result.errors:
            print(f"Errors: {[str(e) for e in result.errors]}")
            return False
        else:
            print("✓ No errors in GraphQL execution")

        # Test response data structure
        response_data = {"data": result.data}
        if result.errors:
            response_data["errors"] = [str(error) for error in result.errors]

        print(f"Response structure: {list(response_data.keys())}")
        print("\n🎉 GRAPHQL TEST PASSED! GraphQL should work in Vercel.")
        return True

    except Exception as e:
        print(f"✗ GraphQL execution failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_graphql_execution()
