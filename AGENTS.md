# AI Coding Agent Guidelines for AW Client Report Portal

## Project Overview
This is a Flask web application for Windbrook Solutions that generates polished PDF financial reports (SACS cashflow and TCC net worth statements) for clients. The app manages client profiles, quarterly data entry, live calculations, and PDF downloads matching specific visual layouts.

## Architecture & Data Flow
- **Backend**: Flask routes handle CRUD operations for clients, accounts, liabilities, and reports
- **Database**: SQLite with tables: `clients`, `accounts`, `liabilities`, `reports` (report data stored as JSON)
- **PDF Generation**: ReportLab creates custom layouts with circles, bubbles, and arrows mimicking Canva designs
- **Frontend**: Jinja2 templates with custom CSS using brand colors (navy #1B2E4B, gold #C8A84B)
- **Data Flow**: Client setup → Account/liability configuration → Quarterly balance entry → Calculation → PDF generation → Storage

## Key Calculations
- **Excess** = Monthly Inflow - Monthly Outflow
- **Private Reserve Target** = (6 × Monthly Expenses) + Insurance Deductibles
- **Retirement Totals**: Sum of client1/client2 retirement account balances
- **Non-Retirement Total**: Non-retirement accounts only (excludes trust)
- **Grand Total** = Retirement1 + Retirement2 + Non-Retirement + Trust
- **Liabilities**: Listed separately, NOT deducted from net worth

## Development Workflow
- **Setup**: `pip install -r requirements.txt && python app.py` (runs on http://localhost:5000)
- **Database**: Auto-initializes on first run with demo data; uses `DB_PATH` env var for persistence
- **Deployment**: Railway with `PORT` env var; Procfile uses `gunicorn app:app --bind 0.0.0.0:$PORT`
- **Debugging**: Flask debug mode enabled by default; check browser console for JS errors

## Code Patterns & Conventions
- **Money Formatting**: Use `fmt()` function: `f'${int(val):,}'` (e.g., `$1,234,567`)
- **Account Categories**: `retirement` (with `owner: client1/client2`), `non-retirement`, `trust`
- **Form Handling**: Arrays like `account_type[]`, `account_category[]` parsed with `request.form.getlist()`
- **Template Filters**: Custom `selectattr`/`rejectattr` for filtering lists by attributes
- **PDF Colors**: Predefined constants (NAVY, GOLD, GREEN, RED, etc.) in `pdf_generator.py`
- **Error Handling**: Basic try/except for date parsing; use `abort(404)` for missing resources
- **File Structure**: `app.py` (routes), `db.py` (SQLite helpers), `pdf_generator.py` (ReportLab logic), `templates/` (Jinja2), `static/` (CSS/JS)

## Integration Points
- **ReportLab**: Canvas-based drawing for PDFs; use `io.BytesIO()` for in-memory generation
- **SQLite**: Row factory returns dict-like objects; use `?` placeholders for parameters
- **Jinja2**: Context processors inject globals like `now`; custom filters for list operations
- **Flask**: `send_file()` for PDF downloads; `jsonify()` for API responses; `url_for()` for routing

## Common Tasks
- **Add New Field**: Update DB schema in `db.py`, form in template, route logic in `app.py`, PDF drawing in `pdf_generator.py`
- **Modify Calculations**: Change formulas in `generate_report` route, ensure PDF reflects updates
- **Style Changes**: Update CSS variables in `base.html` for consistent branding
- **PDF Layout**: Edit drawing functions in `pdf_generator.py`; test with sample data from seeded clients

## References
- `README.md`: Business logic and deployment details
- `app.py`: Route structure and calculation logic
- `db.py`: Schema and seeding patterns
- `pdf_generator.py`: PDF layout examples (SACS page 1 cashflow diagram, TCC account bubbles)
- `templates/base.html`: CSS variables and component patterns
