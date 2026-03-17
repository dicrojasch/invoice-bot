# Invoice Bot - On-Demand WhatsApp Automation

This project is a lightweight automation tool designed to run on a Raspberry Pi. It orchestrates the **Evolution API** (Node.js) using a **Python** controller to send WhatsApp messages only when needed, minimizing RAM and CPU usage.

## Architecture

To optimize resources, this bot does not run 24/7. The Python script:
1. Starts the Evolution API server.
2. Waits for the service to be ready.
3. Sends the scheduled invoices.
4. Shuts down the server immediately after completion.

---

## Prerequisites

- **Hardware**: Raspberry Pi (any model with Node.js support).
- **Environment**: Linux (Ubuntu/Raspberry Pi OS).
- **Software**:
  - Node.js (v20.x or higher)
  - Python 3.x
  - Git
  - PM2 (Optional, for manual debugging)

---

## Initial Setup
### Install Node.js
Install the full Node.js environment (v20 is recommended for Evolution API):

```bash
# Install NVM (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Reload your profile to use NVM
source ~/.bashrc

# Install Node 20 (This will definitely include npm)
nvm install 20
nvm use 20

# Verify installation
node -v
npm -v

# 1. Generate the Prisma Client based on your .env configuration
# Copy the postgres schema as the main schema
cp prisma/postgresql-schema.prisma prisma/schema.prisma

## This creates the missing 'Contact', 'Message', and 'Instance' types
npx prisma generate

## Sync the schema with your local SQLite database
## This will create the 'db.sqlite' file if it doesn't exist
npx prisma db push

## Now try to build the project again
npm run build


### 2. Evolution API (The Engine)
Clone and build the API in your repos folder:

```bash
cd /home/diego/repos/
git clone [https://github.com/EvolutionAPI/evolution-api.git](https://github.com/EvolutionAPI/evolution-api.git)
cd evolution-api
cp .env.example .env
npm install
npm run build
```

---

## Usage

To generate and send invoices, run the `generate_bills.py` script. You can provide optional parameters for the year, month, validation mode, and filtering.

### Basic Usage
Defaults to year "2026", month "Marzo", and sends to the validation number.
```bash
python src/generate_bills.py
```

### Advanced Usage
```bash
# Set specific year and month
python src/generate_bills.py --year 2025 --month Diciembre

# Send directly to responsible phones (skip validation)
python src/generate_bills.py --no-validate

# Process specific bills by their execution ID
python src/generate_bills.py --ids 1,19

# Only list available bills from the spreadsheet without processing them
python src/generate_bills.py --list

# Control logging verbosity (DEBUG, INFO, WARNING, ERROR)
python src/generate_bills.py --log DEBUG
```

### Logging
The project uses a structured logging system. Logs identify the module and, where applicable, the specific bill ID being processed:
`[INFO][generate_bills] [id=19] Sending to Whatsapp...`

By default, internal Google Sheets operations are logged at `DEBUG` level to keep the output clean. Use `--log DEBUG` to see all details.