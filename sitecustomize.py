# Railway deployment path setup - DO NOT REMOVE
# This file is automatically imported by Python on startup and ensures
# that Railway can find our Django modules during deployment.
# Without this, Railway deployments fail with import errors.

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
