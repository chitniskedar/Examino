"""
seed_from_drive.py — Pull every PDF from the askbookie_db Google Drive folder
and seed them into SmartStudy's SQLite database.

Setup (one-time):
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pypdf

Usage:
  python seed_from_drive.py --folder-id <FOLDER_ID> [--creds credentials.json]

How to get your FOLDER_ID:
  Open the Drive folder in your browser.
  The URL looks like: https://drive.google.com/drive/folders/1ABCxyz...
  The long string after /folders/ is your FOLDER_ID.

How to get credentials.json:
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable "Google Drive API"
  3. Create OAuth 2.0 credentials (Desktop app) → Download as credentials.json
  4. Place credentials.json next to this script.
"""

import os
import io
import argparse
import sys
import time

# ── Google Drive ──────────────────────────────────────────────────────────────
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    print("❌  Missing Google libraries. Run:")
    print("    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

try:
    import pypdf
except ImportError:
    print("❌  Missing pypdf. Run:  pip install pypdf")
    sys.exit(1)

# ── SmartStudy modules (must run from smartstudy/ directory) ─────────────────
sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, save_questions, count_questions, SessionLocal
from question_engine import generate_questions

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
TOKEN_FILE = "token.json"


# ── Auth ──────────────────────────────────────────────────────────────────────

def get_drive_service(creds_file: str):
    """Authenticate and return a Drive API service object."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"✓ Auth token saved to {TOKEN_FILE}")

    return build("drive", "v3", credentials=creds)


# ── Drive helpers ─────────────────────────────────────────────────────────────

def list_items(service, folder_id: str) -> list[dict]:
    """List all files and subfolders inside a Drive folder."""
    items = []
    page_token = None
    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def download_pdf(service, file_id: str) -> bytes:
    """Download a Drive file as bytes."""
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF byte string."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            pages.append(t.strip())
    return "\n\n".join(pages)


# ── Seeder ────────────────────────────────────────────────────────────────────

def seed_folder(service, folder_id: str, subject_name: str, db, stats: dict, depth: int = 0):
    """
    Recursively walk a Drive folder tree.
    For each PDF found: download → extract text → generate questions → save to DB.
    """
    indent = "  " * depth
    items = list_items(service, folder_id)

    for item in sorted(items, key=lambda x: x["name"]):
        name = item["name"]
        mime = item["mimeType"]

        if mime == "application/vnd.google-apps.folder":
            # Treat folder name as subject (top-level) or sub-topic
            sub_subject = name if depth == 0 else subject_name
            print(f"{indent}📁 {name}/")
            seed_folder(service, item["id"], sub_subject, db, stats, depth + 1)

        elif mime == "application/pdf" or name.lower().endswith(".pdf"):
            label = f"{subject_name} / {name}"
            print(f"{indent}  📄 {name} — downloading...", end="", flush=True)

            try:
                pdf_bytes = download_pdf(service, item["id"])
                text = extract_text_from_pdf(pdf_bytes)

                if len(text.split()) < 30:
                    print(f" ⚠️  too little text ({len(text.split())} words), skipping")
                    stats["skipped"] += 1
                    continue

                print(f" {len(text.split())} words → generating questions...", end="", flush=True)

                questions = generate_questions(
                    text,
                    num_questions=15,
                    difficulty="medium",
                )
                save_questions(questions, source_file=label, db=db)

                print(f" ✓ {len(questions)} questions saved")
                stats["files"] += 1
                stats["questions"] += len(questions)

            except Exception as e:
                print(f" ✗ ERROR: {e}")
                stats["errors"] += 1

            time.sleep(0.3)  # polite rate limiting

        else:
            # Non-PDF file — skip silently
            pass


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed SmartStudy DB from a Google Drive folder")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID (from the URL)")
    parser.add_argument("--creds", default="credentials.json", help="Path to OAuth credentials.json")
    parser.add_argument("--dry-run", action="store_true", help="List files without downloading")
    args = parser.parse_args()

    if not os.path.exists(args.creds):
        print(f"❌  Credentials file not found: {args.creds}")
        print("    Download it from Google Cloud Console → APIs & Services → Credentials")
        sys.exit(1)

    print("🔐 Authenticating with Google Drive...")
    service = get_drive_service(args.creds)
    print("✓  Connected to Google Drive\n")

    if args.dry_run:
        print("🔍 DRY RUN — listing files only:\n")
        def dry_list(fid, depth=0):
            for item in sorted(list_items(service, fid), key=lambda x: x["name"]):
                indent = "  " * depth
                icon = "📁" if "folder" in item["mimeType"] else "📄"
                print(f"{indent}{icon} {item['name']}")
                if "folder" in item["mimeType"]:
                    dry_list(item["id"], depth + 1)
        dry_list(args.folder_id)
        return

    print("🗄️  Initialising database...")
    init_db()
    db = SessionLocal()
    before = count_questions(db)
    print(f"   Questions in DB before seeding: {before}\n")

    stats = {"files": 0, "questions": 0, "skipped": 0, "errors": 0}

    print(f"📂 Walking Drive folder: {args.folder_id}\n")
    try:
        seed_folder(service, args.folder_id, subject_name="General", db=db, stats=stats)
    finally:
        db.close()

    after_db = SessionLocal()
    after = count_questions(after_db)
    after_db.close()

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Seeding complete!
   PDFs processed : {stats['files']}
   Questions added: {after - before}
   Total in DB    : {after}
   Skipped        : {stats['skipped']}
   Errors         : {stats['errors']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run the SmartStudy server:
  uvicorn main:app --reload
""")


if __name__ == "__main__":
    main()