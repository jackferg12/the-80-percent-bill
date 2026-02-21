# Google Sheets Setup (Required for Saving Pledges)

**Important:** A plain spreadsheet URL only allows **read** access. To **write** (save pledges) to Google Sheets, you must use **Service Account** authentication.

## Step 1: Enable Google APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select an existing one
3. Enable these APIs:
   - **Google Sheets API** (APIs & Services → Library → search "Sheets")
   - **Google Drive API** (APIs & Services → Library → search "Drive")

## Step 2: Create a Service Account

1. Go to [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials** → **Service account**
3. Name it (e.g., "80-percent-bill-app") → **Create and Continue**
4. Skip the optional steps → **Done**
5. Click the new service account → **Keys** tab → **Add Key** → **Create new key**
6. Choose **JSON** → **Create** (downloads a `.json` file)
7. **Copy the `client_email`** from the JSON file (looks like `xxx@xxx.iam.gserviceaccount.com`)

## Step 3: Share Your Spreadsheet

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1yH7yjNuVJmaoYZzwcuGpSc3xvH-YsRUMDZpqGHC_2NQ/
2. Click **Share**
3. Add the service account email (`client_email` from step 2)
4. Give it **Editor** permission
5. Uncheck "Notify people" → **Share**

## Step 4: Update secrets.toml

**Option A – Use the helper script (easiest):**
```bash
python scripts/convert_service_account_to_toml.py path/to/your-key.json
```
Then paste the output into `.streamlit/secrets.toml` and replace `YOUR_SHEET_ID` with `1yH7yjNuVJmaoYZzwcuGpSc3xvH-YsRUMDZpqGHC_2NQ`.

**Option B – Manual setup:** Replace the `[connections.gsheets]` section with the service account format. Copy values from your downloaded JSON:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/1yH7yjNuVJmaoYZzwcuGpSc3xvH-YsRUMDZpqGHC_2NQ/edit#gid=0"
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = """
-----BEGIN PRIVATE KEY-----
(paste full key including BEGIN/END lines)
-----END PRIVATE KEY-----
"""
client_email = "xxx@xxx.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
```

## Step 5: Restart the App

```bash
streamlit run 80percentapp.py
```

Pledges should now save to your spreadsheet.
