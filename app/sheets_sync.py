# sheets_sync.py
# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

from google.oauth2 import service_account
from googleapiclient.discovery import build
from .models import Appointment, SessionLocal
import os


SHEET_ID = "1puAsC935rHZ-Sv2hMhbvTO7ZDjzUL_r9dJkttsioxao"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # goes to whatsapp_ai_bot/
SERVICE_ACCOUNT_FILE = os.path.join(ROOT_DIR, "whatsapp-bot-credentials.json")

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("sheets", "v4", credentials=credentials)
sheet = service.spreadsheets()


def sync_appt_to_sheet():
    db = SessionLocal()
    try:
        # 1️⃣ Fetch all appointments from the DB
        appointments = db.query(Appointment).all()

        # 2️⃣ Get all existing sheet rows including header
        result = sheet.values().get(
            spreadsheetId=SHEET_ID,
            range="Sheet1!A1:F1000"
        ).execute()
        rows = result.get("values", [])

        # 3️⃣ Separate header and data
        header = rows[0] if rows else ["type", "date", "time", "clientName", "phone", "status"]
        data_rows = rows[1:] if len(rows) > 1 else []

        # 4️⃣ Keep only rows where status column (column 6) is blank
        rows_to_keep = []
        for row in data_rows:
            # If the row has less than 6 columns, treat status as blank
            status = row[5] if len(row) > 5 else ""
            if status.strip() == "":
                rows_to_keep.append(row)


        # 5️⃣ Add all appointments from DB (status blank)
        for a in appointments:
            rows_to_keep.append([
                a.type or "",
                str(a.date) or "",
                str(a.time) or "",
                a.name or "",
                a.phone or "",
                ""  # status blank
            ])

        # 6️⃣ Write header + rows back to sheet
        sheet.values().update(
            spreadsheetId=SHEET_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": [header] + rows_to_keep}
        ).execute()

        #print(f"Synced {len(appointments)} appointments! Rows with status removed.")

    finally:
        db.close()


def test_connection():
    result = sheet.get(spreadsheetId=SHEET_ID).execute()
    print("Connected!")
    print("Spreadsheet title:", result["properties"]["title"])

if __name__ == "__main__":
    test_connection()
    sync_appt_to_sheet()

