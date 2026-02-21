# The 80% Bill

**Website:** https://80percentbill.streamlit.app/

A Streamlit web app for collecting pledges in support of "The 80% Bill"—a package of popular legislation that polls show at least 80% of American voters support. Users can add their name to the pledge and browse the bills.

## Overview

- **Pledge flow**: Users enter their congressional district and representative, then sign with name and email. Data is stored in Google Sheets with a local CSV backup.
- **Bill browser**: Displays 20 articles (bills) with descriptions and links to congress.gov.
- **Hosting**: Deployed on [Streamlit Community Cloud](https://80percentbill.streamlit.app/).

## Tech Stack

- **Streamlit** – Web app framework
- **Google Sheets** – Primary storage for pledges (via `st-gsheets-connection`)
- **Geocodio API** – Congressional district lookup (address → district + rep)
- **OpenStreetMap Nominatim** – Address search/autocomplete
- **Gmail SMTP** – Email verification (optional; app runs without it)

---

## Development Setup

### Prerequisites

- Python 3.8+
- [Geocodio](https://www.geocod.io/) API key (optional, for address lookup)
- Google Sheets set up for pledges and backup
- Gmail app password (optional, for email verification)

### 1. Clone and install dependencies

```bash
cd the-80-percent-bill
pip install -r requirements.txt
```

### 2. Configure secrets

Create a `.streamlit` directory and a `secrets.toml` file:

```bash
mkdir -p .streamlit
```

Create `.streamlit/secrets.toml` with:

**⚠️ Spreadsheet URL alone is read-only.** To **save** pledges, you must use **Service Account** auth. See **[SECRETS_SETUP.md](SECRETS_SETUP.md)** for full instructions.

```toml
GEOCODIO_API_KEY = "your-geocodio-api-key"
EMAIL_PASSWORD = ""

[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0"
type = "service_account"
# + project_id, private_key, client_email, etc. from JSON key file

BACKUP_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0"
```

**Helper:** `python scripts/convert_service_account_to_toml.py path/to/key.json` to convert your JSON key to TOML format.

> **Important:** Do not commit `secrets.toml`. It is listed in `.gitignore`.

### 3. Run the app locally

```bash
streamlit run 80percentapp.py
```

Streamlit will start a local server (usually at **http://localhost:8501**). The app will open in your browser.

### Development tips

- **No Geocodio key**: The app still works. Users enter district code (e.g. `NY-14`) and rep name manually.
- **No email password**: Verification is skipped; pledges are saved normally.
- **No gsheets setup**: The app will fail when saving pledges. Use test sheets or mock data for UI work.
- **Logo**: Place `logo.png` or `logo.jpg` in the project root for the sidebar image.

---

## Project Structure

| File | Purpose |
|------|---------|
| `80percentapp.py` | Main Streamlit app (pledge form, bill list, theming) |
| `backup_service.py` | Saves pledges to a backup Google Sheet ("the vault") |
| `pledges.csv` | Local CSV backup (if used) |
| `requirements.txt` | Python dependencies |

---

## Deployment

The app is deployed on **Streamlit Community Cloud** at https://80percentbill.streamlit.app/. Secrets are configured in the Streamlit Cloud dashboard. A GitHub Actions workflow (`keep_alive.yml`) pings the app every 10 minutes to reduce cold starts.

---

## License

See repository for license details.
