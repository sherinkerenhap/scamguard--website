SCAMGUARD DATABASE SETUP

1. Open MySQL Workbench.
2. Open database/scamguard_database.sql.
3. Run the complete SQL file.
4. It creates the 'scamguard' database and:
   - scam_messages
   - scan_history
5. It also inserts sample spam/ham records.

Before starting Flask, set your MySQL password in the terminal:

PowerShell:
$env:SCAMGUARD_DB_PASSWORD="YOUR_MYSQL_PASSWORD"

If your MySQL root account has no password, use:
$env:SCAMGUARD_DB_PASSWORD=""

Optional:
$env:SCAMGUARD_DB_USER="root"
$env:SCAMGUARD_DB_HOST="localhost"
$env:SCAMGUARD_DB_NAME="scamguard"

The existing website pages and frontend files are unchanged.
The Flask backend now saves completed message/URL scan results into scan_history when MySQL is available.
