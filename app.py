from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, abort
from db import init_db, seed_demo_data, get_db
from pdf_generator import draw_sacs_pdf, draw_tcc_pdf
import json
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'aw-portal-secret-2026'

@app.context_processor
def inject_globals():
    return {'now': datetime.now()}

@app.template_filter('selectattr')
def selectattr_filter(items, attr, value=None, op='equalto'):
    return [i for i in items if (dict(i).get(attr) == value if value is not None else dict(i).get(attr))]

@app.template_filter('rejectattr')
def rejectattr_filter(items, attr):
    return [i for i in items if not dict(i).get(attr)]

# ─── CLIENT LIST ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    clients = db.execute('''
        SELECT c.*, r.report_date as last_report_date
        FROM clients c
        LEFT JOIN (
            SELECT client_id, MAX(report_date) as report_date FROM reports GROUP BY client_id
        ) r ON c.id = r.client_id
        ORDER BY c.name
    ''').fetchall()
    db.close()
    return render_template('index.html', clients=clients)

# ─── CLIENT PROFILE ────────────────────────────────────────────────────────────
@app.route('/client/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        db = get_db()
        d = request.form
        is_married = 1 if d.get('is_married') else 0

        # Calculate age
        dob = d.get('dob', '')
        age = 0
        if dob:
            try:
                born = datetime.strptime(dob, '%Y-%m-%d')
                age = (datetime.now() - born).days // 365
            except: pass

        dob2 = d.get('dob2', '')
        age2 = 0
        if dob2 and is_married:
            try:
                born2 = datetime.strptime(dob2, '%Y-%m-%d')
                age2 = (datetime.now() - born2).days // 365
            except: pass

        c = db.execute('''INSERT INTO clients
            (name, name2, dob, dob2, age, age2, ssn_last4, ssn_last4_2,
             monthly_salary, monthly_expenses, insurance_deductibles, is_married)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (d['name'], d.get('name2', '') if is_married else '',
             dob, dob2 if is_married else '',
             age, age2 if is_married else 0,
             d.get('ssn_last4', ''), d.get('ssn_last4_2', '') if is_married else '',
             float(d.get('monthly_salary', 0) or 0),
             float(d.get('monthly_expenses', 0) or 0),
             float(d.get('insurance_deductibles', 0) or 0),
             is_married))
        client_id = c.lastrowid

        # Save accounts
        _save_accounts(db, client_id, request.form)
        # Save liabilities
        _save_liabilities(db, client_id, request.form)

        db.commit()
        db.close()
        return redirect(url_for('client_profile', client_id=client_id))
    return render_template('client_form.html', client=None, accounts=[], liabilities=[])

@app.route('/client/<int:client_id>')
def client_profile(client_id):
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id=?', (client_id,)).fetchone()
    if not client:
        abort(404)
    accounts = db.execute('SELECT * FROM accounts WHERE client_id=?', (client_id,)).fetchall()
    liabilities = db.execute('SELECT * FROM liabilities WHERE client_id=?', (client_id,)).fetchall()
    reports = db.execute('SELECT * FROM reports WHERE client_id=? ORDER BY report_date DESC LIMIT 5', (client_id,)).fetchall()
    db.close()
    return render_template('client_profile.html', client=client, accounts=accounts, liabilities=liabilities, reports=reports)

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id=?', (client_id,)).fetchone()
    if not client:
        abort(404)
    accounts = db.execute('SELECT * FROM accounts WHERE client_id=?', (client_id,)).fetchall()
    liabilities = db.execute('SELECT * FROM liabilities WHERE client_id=?', (client_id,)).fetchall()

    if request.method == 'POST':
        d = request.form
        is_married = 1 if d.get('is_married') else 0
        dob = d.get('dob', '')
        age = 0
        if dob:
            try:
                born = datetime.strptime(dob, '%Y-%m-%d')
                age = (datetime.now() - born).days // 365
            except: pass
        dob2 = d.get('dob2', '')
        age2 = 0
        if dob2 and is_married:
            try:
                born2 = datetime.strptime(dob2, '%Y-%m-%d')
                age2 = (datetime.now() - born2).days // 365
            except: pass

        db.execute('''UPDATE clients SET
            name=?, name2=?, dob=?, dob2=?, age=?, age2=?,
            ssn_last4=?, ssn_last4_2=?, monthly_salary=?, monthly_expenses=?,
            insurance_deductibles=?, is_married=?
            WHERE id=?''',
            (d['name'], d.get('name2', '') if is_married else '',
             dob, dob2 if is_married else '', age, age2 if is_married else 0,
             d.get('ssn_last4', ''), d.get('ssn_last4_2', '') if is_married else '',
             float(d.get('monthly_salary', 0) or 0),
             float(d.get('monthly_expenses', 0) or 0),
             float(d.get('insurance_deductibles', 0) or 0),
             is_married, client_id))

        db.execute('DELETE FROM accounts WHERE client_id=?', (client_id,))
        db.execute('DELETE FROM liabilities WHERE client_id=?', (client_id,))
        _save_accounts(db, client_id, request.form)
        _save_liabilities(db, client_id, request.form)
        db.commit()
        db.close()
        return redirect(url_for('client_profile', client_id=client_id))

    db.close()
    return render_template('client_form.html', client=client, accounts=accounts, liabilities=liabilities)

# ─── GENERATE REPORT ───────────────────────────────────────────────────────────
@app.route('/client/<int:client_id>/report', methods=['GET', 'POST'])
def generate_report(client_id):
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id=?', (client_id,)).fetchone()
    accounts = db.execute('SELECT * FROM accounts WHERE client_id=?', (client_id,)).fetchall()
    liabilities = db.execute('SELECT * FROM liabilities WHERE client_id=?', (client_id,)).fetchall()
    last_report = db.execute('SELECT * FROM reports WHERE client_id=? ORDER BY report_date DESC LIMIT 1', (client_id,)).fetchone()

    if request.method == 'POST':
        d = request.form
        inflow = float(d.get('inflow', 0) or 0)
        outflow = float(d.get('outflow', 0) or 0)
        excess = inflow - outflow
        private_reserve_balance = float(d.get('private_reserve_balance', 0) or 0)
        insurance_ded = float(client['insurance_deductibles'] or 0)
        private_reserve_target = (6 * outflow) + insurance_ded
        investment_balance = float(d.get('investment_balance', 0) or 0)

        # Gather account balances
        account_balances = {}
        for acc in accounts:
            key = f'acc_{acc["id"]}'
            account_balances[str(acc['id'])] = float(d.get(key, 0) or 0)

        ret1_total = sum(account_balances.get(str(a['id']), 0) for a in accounts
                         if a['account_category'] == 'retirement' and a['owner'] == 'client1')
        ret2_total = sum(account_balances.get(str(a['id']), 0) for a in accounts
                         if a['account_category'] == 'retirement' and a['owner'] == 'client2')
        non_ret_total = sum(account_balances.get(str(a['id']), 0) for a in accounts
                            if a['account_category'] == 'non-retirement')
        trust_value = float(d.get('trust_value', 0) or 0)
        grand_total = ret1_total + ret2_total + non_ret_total + trust_value

        # Liabilities
        liability_balances = {}
        for lib in liabilities:
            key = f'lib_{lib["id"]}'
            liability_balances[str(lib['id'])] = float(d.get(key, 0) or 0)
        liabilities_total = sum(liability_balances.values())

        report_data = json.dumps({
            'account_balances': account_balances,
            'liability_balances': liability_balances,
            'trust_value': trust_value,
            'investment_balance': investment_balance,
        })

        quarter = d.get('quarter', f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year}")

        db.execute('''INSERT INTO reports
            (client_id, quarter, inflow, outflow, excess, private_reserve_balance,
             private_reserve_target, grand_total, liabilities_total, report_data)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (client_id, quarter, inflow, outflow, excess,
             private_reserve_balance, private_reserve_target,
             grand_total, liabilities_total, report_data))
        db.execute('UPDATE clients SET last_report_date=CURRENT_TIMESTAMP WHERE id=?', (client_id,))
        report_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()
        db.close()
        return redirect(url_for('report_view', client_id=client_id, report_id=report_id))

    db.close()
    return render_template('generate_report.html',
                           client=client, accounts=accounts, liabilities=liabilities,
                           last_report=last_report)

@app.route('/client/<int:client_id>/report/<int:report_id>')
def report_view(client_id, report_id):
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id=?', (client_id,)).fetchone()
    report = db.execute('SELECT * FROM reports WHERE id=? AND client_id=?', (report_id, client_id)).fetchone()
    accounts = db.execute('SELECT * FROM accounts WHERE client_id=?', (client_id,)).fetchall()
    liabilities = db.execute('SELECT * FROM liabilities WHERE client_id=?', (client_id,)).fetchall()
    if not report:
        abort(404)
    report_data = json.loads(report['report_data'] or '{}')
    db.close()
    return render_template('report_view.html',
                           client=client, report=report, accounts=accounts,
                           liabilities=liabilities, report_data=report_data)

# ─── PDF DOWNLOADS ─────────────────────────────────────────────────────────────
@app.route('/client/<int:client_id>/report/<int:report_id>/sacs.pdf')
def download_sacs(client_id, report_id):
    pdf_data = _build_pdf_data(client_id, report_id)
    if not pdf_data:
        abort(404)
    buf = draw_sacs_pdf(pdf_data)
    return send_file(buf, mimetype='application/pdf',
                     download_name=f"SACS_{pdf_data['client_name'].replace(' ', '_')}_{pdf_data['quarter']}.pdf")

@app.route('/client/<int:client_id>/report/<int:report_id>/tcc.pdf')
def download_tcc(client_id, report_id):
    pdf_data = _build_pdf_data(client_id, report_id)
    if not pdf_data:
        abort(404)
    buf = draw_tcc_pdf(pdf_data)
    return send_file(buf, mimetype='application/pdf',
                     download_name=f"TCC_{pdf_data['client_name'].replace(' ', '_')}_{pdf_data['quarter']}.pdf")

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def _build_pdf_data(client_id, report_id):
    db = get_db()
    client = db.execute('SELECT * FROM clients WHERE id=?', (client_id,)).fetchone()
    report = db.execute('SELECT * FROM reports WHERE id=? AND client_id=?', (report_id, client_id)).fetchone()
    accounts = db.execute('SELECT * FROM accounts WHERE client_id=?', (client_id,)).fetchall()
    liabilities = db.execute('SELECT * FROM liabilities WHERE client_id=?', (client_id,)).fetchall()
    db.close()
    if not report or not client:
        return None

    rd = json.loads(report['report_data'] or '{}')
    ab = rd.get('account_balances', {})
    lb = rd.get('liability_balances', {})

    ret1 = [{'type': a['account_type'], 'last4': a['last4'],
              'balance': ab.get(str(a['id']), 0), 'institution': a['institution']}
            for a in accounts if a['account_category'] == 'retirement' and a['owner'] == 'client1']
    ret2 = [{'type': a['account_type'], 'last4': a['last4'],
              'balance': ab.get(str(a['id']), 0), 'institution': a['institution']}
            for a in accounts if a['account_category'] == 'retirement' and a['owner'] == 'client2']
    nr = [{'type': a['account_type'], 'last4': a['last4'],
           'balance': ab.get(str(a['id']), 0), 'institution': a['institution']}
          for a in accounts if a['account_category'] == 'non-retirement']
    libs = [{'type': l['liability_type'], 'rate': l['interest_rate'],
             'balance': lb.get(str(l['id']), 0)}
            for l in liabilities]

    ret1_total = sum(a['balance'] for a in ret1)
    ret2_total = sum(a['balance'] for a in ret2)
    non_ret_total = sum(a['balance'] for a in nr)

    return {
        'client_name': client['name'] + (' & ' + client['name2'] if client['is_married'] and client['name2'] else ''),
        'report_date': report['report_date'][:10] if report['report_date'] else '',
        'quarter': report['quarter'] or '',
        'inflow': report['inflow'],
        'outflow': report['outflow'],
        'excess': report['excess'],
        'private_reserve_balance': report['private_reserve_balance'],
        'private_reserve_target': report['private_reserve_target'],
        'investment_balance': rd.get('investment_balance', 0),
        'trust_value': rd.get('trust_value', 0),
        'grand_total': report['grand_total'],
        'liabilities_total': report['liabilities_total'],
        'is_married': client['is_married'],
        'client1': {'name': client['name'], 'dob': client['dob'], 'age': client['age'], 'ssn': client['ssn_last4']},
        'client2': {'name': client['name2'], 'dob': client['dob2'], 'age': client['age2'], 'ssn': client['ssn_last4_2']} if client['is_married'] else {},
        'retirement1_accounts': ret1,
        'retirement2_accounts': ret2,
        'non_retirement_accounts': nr,
        'liabilities': libs,
        'ret1_total': ret1_total,
        'ret2_total': ret2_total,
        'non_ret_total': non_ret_total,
    }

def _save_accounts(db, client_id, form):
    types = form.getlist('account_type[]')
    categories = form.getlist('account_category[]')
    owners = form.getlist('account_owner[]')
    last4s = form.getlist('account_last4[]')
    institutions = form.getlist('account_institution[]')
    for i in range(len(types)):
        if types[i]:
            db.execute('INSERT INTO accounts (client_id, owner, account_type, account_category, last4, institution) VALUES (?,?,?,?,?,?)',
                       (client_id, owners[i] if i < len(owners) else 'client1',
                        types[i], categories[i] if i < len(categories) else 'non-retirement',
                        last4s[i] if i < len(last4s) else '',
                        institutions[i] if i < len(institutions) else ''))

def _save_liabilities(db, client_id, form):
    lib_types = form.getlist('liability_type[]')
    lib_rates = form.getlist('liability_rate[]')
    for i in range(len(lib_types)):
        if lib_types[i]:
            db.execute('INSERT INTO liabilities (client_id, liability_type, interest_rate) VALUES (?,?,?)',
                       (client_id, lib_types[i], float(lib_rates[i] if i < len(lib_rates) and lib_rates[i] else 0)))

if __name__ == '__main__':
    init_db()
    seed_demo_data()
    app.run(debug=True, port=5000)
