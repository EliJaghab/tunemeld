#!/usr/bin/env python3
"""
Script to scrub sensitive credentials from git history using git filter-branch
"""

import subprocess
import sys
import re

# Define the sensitive patterns to scrub
CREDENTIAL_PATTERNS = [
    # PostgreSQL Database URLs
    (r'postgresql://postgres:[^@]+@[^/]+/railway', 'postgresql://postgres:REDACTED@REDACTED/railway'),
    
    # Cloudflare tokens and IDs
    (r'HEMtqXKa1hsfGFT7_wR6vFseC5vs6HlQ1UtwEStF', 'REDACTED_CF_API_TOKEN'),
    (r'b8a3bf4fc8e54308300b0fa9b11a41a1', 'REDACTED_CF_ACCOUNT_ID'),
    (r'12a02c4cb50a379e20e15717eb431a72', 'REDACTED_CF_NAMESPACE_ID'),
    
    # Spotify credentials
    (r'943b6c1c8113466d8d004e148b43d857', 'REDACTED_SPOTIFY_CLIENT_ID'),
    (r'6b1492cd2795463097724b1a9458bf32', 'REDACTED_SPOTIFY_CLIENT_SECRET'),
    
    # Generic password patterns in connection strings
    (r'TMvEddPnHxNAtoxkPZmYaKYYawSScutY', 'REDACTED_PASSWORD'),
]

def scrub_file_content(content):
    """Scrub sensitive content from file content"""
    for pattern, replacement in CREDENTIAL_PATTERNS:
        content = re.sub(pattern, replacement, content)
    return content

def main():
    print("🧹 Starting credential scrubbing from git history...")
    print("=" * 60)
    
    # Create the filter script
    filter_script = '''
import sys
import re

CREDENTIAL_PATTERNS = [
    (r'postgresql://postgres:[^@]+@[^/]+/railway', 'postgresql://postgres:REDACTED@REDACTED/railway'),
    (r'HEMtqXKa1hsfGFT7_wR6vFseC5vs6HlQ1UtwEStF', 'REDACTED_CF_API_TOKEN'),
    (r'b8a3bf4fc8e54308300b0fa9b11a41a1', 'REDACTED_CF_ACCOUNT_ID'),
    (r'12a02c4cb50a379e20e15717eb431a72', 'REDACTED_CF_NAMESPACE_ID'),
    (r'943b6c1c8113466d8d004e148b43d857', 'REDACTED_SPOTIFY_CLIENT_ID'),
    (r'6b1492cd2795463097724b1a9458bf32', 'REDACTED_SPOTIFY_CLIENT_SECRET'),
    (r'TMvEddPnHxNAtoxkPZmYaKYYawSScutY', 'REDACTED_PASSWORD'),
]

content = sys.stdin.read()
for pattern, replacement in CREDENTIAL_PATTERNS:
    content = re.sub(pattern, replacement, content)
sys.stdout.write(content)
    '''
    
    with open('filter_script.py', 'w') as f:
        f.write(filter_script)
    
    # Run git filter-branch
    cmd = [
        'git', 'filter-branch', '--force', '--tree-filter',
        'find . -type f -name "*.py" -exec python3 ../filter_script.py < {} > {}.tmp \\; && mv {}.tmp {} || true',
        '--', '--all'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        print(f"Git filter-branch result: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
            
    except Exception as e:
        print(f"Error running git filter-branch: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()