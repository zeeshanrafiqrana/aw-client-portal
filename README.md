# AW Client Report Portal

A portal for Windbrook Solutions to generate polished SACS (cashflow) and TCC (net worth) PDF reports in minutes.

## Features

- **Client Management** — Store each client's profile once: names, DOB, SSN last 4, account structure
- **Quarterly Data Entry** — Structured form pre-populated with static data; enter only current balances
- **Live Calculations** — Excess, PR Target, retirement totals, grand net worth update in real time
- **PDF Generation** — Download SACS and TCC reports matching the existing template layout
- **Report History** — Re-download any previous quarterly report

## SACS Calculations
- Monthly Excess = Inflow − Outflow
- Private Reserve Target = (6 × monthly expenses) + insurance deductibles
- Liabilities displayed separately — NOT subtracted from net worth

## TCC Calculations
- Client 1 Retirement Total = sum of Client 1 retirement account balances
- Client 2 Retirement Total = sum of Client 2 retirement account balances  
- Non-Retirement Total = non-retirement accounts only (trust excluded)
- Grand Total = Retirement1 + Retirement2 + Non-Retirement + Trust
- Liabilities listed separately as a distinct section

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## Deploy to Railway

1. Push to GitHub
2. Connect repo to Railway
3. Set `PORT` environment variable (Railway does this automatically)
4. Add a volume at `/app` and set `DB_PATH=/app/portal.db`

## Gaps Identified

1. **Canva Export** — The PRD marks this as discussed but not confirmed. PDF download is implemented; Canva API integration would require a `CANVA_API_KEY` and their Design API (currently in limited beta).

2. **PDF Visual Layout** — The original SACS uses circular "bubble" diagrams designed in Canva. The PDF renderer replicates this faithfully using ReportLab shapes. Sample PDFs from the team would allow pixel-perfect matching to the exact original.

3. **Data Point List document** — Rebecca created a field-by-field mapping document (referenced in PRD at timestamp 29:14). Access to this document would allow verification that all field labels and data sources are correctly mapped.

4. **Dropbox Auto-Save** — Not implemented in V1 per the PRD. Would require Dropbox API credentials and folder path mapping per client.

5. **Account Number (Last 4)** — TCC shows last 4 of account numbers on the visual. These are entered during client setup; the PDF generator uses them as-is.
