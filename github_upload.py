import os
import sys
import base64
import json
import urllib.request
import urllib.error

REPO_OWNER = "Pushpendu-Maity"
REPO_NAME = "Final_Year_project"
BRANCH = "main"

EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', '.venv', '.idea', '.vscode'}
EXCLUDE_EXTS = {'.pyc', '.pyo', '.db-journal'}

def upload_file_to_github(token, file_path, rel_path):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{rel_path}"
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    b64_content = base64.b64encode(content).decode('utf-8')
    
    # Check if file already exists to get its SHA
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "MediMind-CDSS-Uploader"
    }
    
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            sha = data.get('sha')
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"  [Warning] Checking {rel_path}: {e}")

    payload = {
        "message": f"Upload {rel_path} for 7th Sem Project",
        "content": b64_content,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha

    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=req_data, headers=headers, method="PUT")
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                print(f"  [✓] Uploaded: {rel_path}")
                return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8', errors='ignore')
        print(f"  [X] Failed {rel_path}: {e.code} - {err_msg}")
        return False

def main():
    print("=" * 60)
    print("     GITHUB API UPLOADER: Pushpendu-Maity/Final_Year_project")
    print("=" * 60)
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("\nTo upload files directly to your GitHub repository without git:")
        print("Please enter your GitHub Personal Access Token (PAT).")
        print("(Generate one at: https://github.com/settings/tokens with 'repo' scope)")
        print()
        token = input("Enter GitHub Personal Access Token: ").strip()
    
    if not token:
        print("Error: No token provided. Exiting.")
        return

    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    files_to_upload = []

    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in EXCLUDE_EXTS:
                continue
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, workspace_dir).replace('\\', '/')
            files_to_upload.append((full_p, rel_p))

    print(f"\nFound {len(files_to_upload)} files to upload to {REPO_OWNER}/{REPO_NAME} on branch '{BRANCH}'...\n")

    success_count = 0
    for full_path, rel_path in files_to_upload:
        if upload_file_to_github(token, full_path, rel_path):
            success_count += 1

    print(f"\nUpload Complete! Successfully uploaded {success_count}/{len(files_to_upload)} files.")
    print(f"Repository Link: https://github.com/{REPO_OWNER}/{REPO_NAME}")

if __name__ == '__main__':
    main()
