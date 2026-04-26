# Secrets Recovery

The API keys and environment variables required to run this application are securely stored in Bitwarden.

**Location in Bitwarden:**
* **Folder:** `Hora`
* **Secure Note Name:** `Telegram-Qwen .env Backup`

## How to Retrieve
1. Open Bitwarden and locate the Secure Note mentioned above.
2. Inside the Secure Note, you will find "Custom Fields" containing the required environment variables.
3. Create a new file named `.env` in the root of this project.
4. Copy each custom field name and value into the `.env` file in the format `KEY=VALUE`.

**Required Fields:**
* `TELEGRAM_BOT_TOKEN`
* `TELEGRAM_ADMIN_ID`
* `MOLTBOOK_API_KEY`
* `MAX_TOOL_TURNS`
* `QWEN_TIMEOUT`
* `MAX_RETRIES`
* `MAX_HISTORY_LENGTH`
* `RATE_LIMIT_MESSAGES`
* `RATE_LIMIT_WINDOW`