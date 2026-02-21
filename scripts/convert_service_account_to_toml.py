#!/usr/bin/env python3
"""
Convert a Google Service Account JSON key file to secrets.toml format.
Usage: python scripts/convert_service_account_to_toml.py path/to/key.json

Add the output to your .streamlit/secrets.toml under [connections.gsheets]
"""

import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_service_account_to_toml.py path/to/service-account.json [spreadsheet_url]")
        sys.exit(1)

    key_path = Path(sys.argv[1])
    if not key_path.exists():
        print(f"Error: File not found: {key_path}")
        sys.exit(1)

    spreadsheet_url = sys.argv[2] if len(sys.argv) > 2 else "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0"

    with open(key_path) as f:
        key = json.load(f)
    print("Add this to .streamlit/secrets.toml:")
    print()
    print("[connections.gsheets]")
    print(f'spreadsheet = "{spreadsheet_url}"')
    print('type = "service_account"')
    print(f'project_id = "{key["project_id"]}"')
    print(f'private_key_id = "{key["private_key_id"]}"')
    # Use TOML multi-line string for private key
    print('private_key = """')
    print(key["private_key"].strip())
    print('"""')
    print(f'client_email = "{key["client_email"]}"')
    print(f'client_id = "{key["client_id"]}"')
    print(f'auth_uri = "{key["auth_uri"]}"')
    print(f'token_uri = "{key["token_uri"]}"')
    print(f'auth_provider_x509_cert_url = "{key["auth_provider_x509_cert_url"]}"')
    print(f'client_x509_cert_url = "{key["client_x509_cert_url"]}"')
    print()
    print("Don't forget to share your spreadsheet with:", key["client_email"])

if __name__ == "__main__":
    main()
