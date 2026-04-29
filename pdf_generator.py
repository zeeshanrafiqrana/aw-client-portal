from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate
import io
import math

# Brand colors
NAVY = colors.HexColor('#1B2E4B')
GOLD = colors.HexColor('#C8A84B')
GREEN = colors.HexColor('#2E7D5E')
RED = colors.HexColor('#C0392B')
BLUE_RESERVE = colors.HexColor('#4f46e5')
LIGHT_GRAY = colors.HexColor('#F4F6F8')
MID_GRAY = colors.HexColor('#8E9BAA')
WHITE = colors.white
DARK_TEXT = colors.HexColor('#1A1A2E')

def fmt(val):
    """Format dollar amount"""
    if val is None:
        return '$0'
    return f'${int(val):,}'

def draw_sacs_pdf(data):
    """Generate SACS cashflow PDF"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    W, H = letter

    # Background
    c.setFillColor(LIGHT_GRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Header bar
    c.setFillColor(NAVY)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)

    # Gold accent line
    c.setFillColor(GOLD)
    c.rect(0, H - 93, W, 3, fill=1, stroke=0)

    # Header text
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(50, H - 50, 'Simple Automated Cash Flow System')
    c.setFont('Helvetica', 12)
    c.drawString(50, H - 70, 'SACS  |  Monthly Cash Flow Overview')

    # Client name and date right-aligned (shifted down to avoid overlap)
    c.setFont('Helvetica-Bold', 13)
    client_name = data.get('client_name', '')
    c.drawRightString(W - 60, H - 70, client_name)
    c.setFont('Helvetica', 11)
    c.drawRightString(W - 60, H - 85, data.get('report_date', ''))

    # -- PAGE 1: Cashflow diagram --
    center_y = H / 2 + 30

    # Draw connecting arrow line (background)
    c.setStrokeColor(MID_GRAY)
    c.setLineWidth(2)
    c.line(50, center_y, W - 50, center_y)

    # INFLOW circle (green)
    inflow_cx = 130
    inflow_cy = center_y
    r_inflow = 85
    c.setFillColor(GREEN)
    c.setStrokeColor(WHITE)
    c.setLineWidth(4)
    c.circle(inflow_cx, inflow_cy, r_inflow, fill=1, stroke=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(inflow_cx, inflow_cy + 20, 'MONTHLY')
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(inflow_cx, inflow_cy + 2, fmt(data.get('inflow', 0)))
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(inflow_cx, inflow_cy - 20, 'INFLOW')
    c.setFont('Helvetica', 9)
    c.drawCentredString(inflow_cx, inflow_cy - 35, 'Take-Home Pay')

    # Arrow from inflow to outflow
    _draw_arrow(c, inflow_cx + r_inflow, center_y, 240, center_y, GOLD)

    # OUTFLOW circle (red)
    outflow_cx = 310
    outflow_cy = center_y
    r_outflow = 85
    c.setFillColor(RED)
    c.setStrokeColor(WHITE)
    c.setLineWidth(4)
    c.circle(outflow_cx, outflow_cy, r_outflow, fill=1, stroke=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(outflow_cx, outflow_cy + 20, 'MONTHLY')
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(outflow_cx, outflow_cy + 2, fmt(data.get('outflow', 0)))
    c.setFont('Helvetica-Bold', 12)
    c.drawCentredString(outflow_cx, outflow_cy - 20, 'OUTFLOW')
    c.setFont('Helvetica', 9)
    c.drawCentredString(outflow_cx, outflow_cy - 35, 'Monthly Expenses')

    # Arrow from outflow to excess
    excess = data.get('excess', 0)
    arrow_color = GREEN if excess >= 0 else RED
    _draw_arrow(c, outflow_cx + r_outflow, center_y, 420, center_y, arrow_color)

    # EXCESS label
    excess_x = 420 + (W - 50 - 420) / 2
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(excess_x, center_y + 30, 'MONTHLY EXCESS')
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(GREEN if excess >= 0 else RED)
    c.drawCentredString(excess_x, center_y + 10, fmt(excess))

    # PRIVATE RESERVE box
    pr_x = W - 220
    pr_y = center_y - 110
    pr_w = 180
    pr_h = 90
    c.setFillColor(BLUE_RESERVE)
    c.setStrokeColor(WHITE)
    c.setLineWidth(3)
    c.roundRect(pr_x, pr_y, pr_w, pr_h, 10, fill=1, stroke=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(pr_x + pr_w/2, pr_y + pr_h - 18, 'PRIVATE RESERVE')
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(pr_x + pr_w/2, pr_y + pr_h - 36, 'Current Balance')
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(pr_x + pr_w/2, pr_y + pr_h - 58, fmt(data.get('private_reserve_balance', 0)))
    c.setFont('Helvetica', 9)
    c.drawCentredString(pr_x + pr_w/2, pr_y + 10, f"Target: {fmt(data.get('private_reserve_target', 0))}")

    # Arrow down to PR box
    _draw_arrow(c, excess_x, center_y - 10, excess_x, pr_y + pr_h + 10, BLUE_RESERVE, vertical=True)

    # Investment account box (bottom)
    inv_bal = data.get('investment_balance', 0)
    inv_x = 50
    inv_y = center_y - 170
    inv_w = 200
    inv_h = 70
    c.setFillColor(NAVY)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.roundRect(inv_x, inv_y, inv_w, inv_h, 8, fill=1, stroke=1)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(inv_x + inv_w/2, inv_y + inv_h - 18, 'SCHWAB INVESTMENT')
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(inv_x + inv_w/2, inv_y + inv_h - 40, fmt(inv_bal))
    c.setFont('Helvetica', 9)
    c.setFillColor(GOLD)
    c.drawCentredString(inv_x + inv_w/2, inv_y + 10, 'Total Portfolio Balance')

    # Footer
    _draw_footer(c, W, H, 'SACS — Confidential | Windbrook Solutions')

    c.showPage()

    # -- PAGE 2: Summary table --
    c.setFillColor(LIGHT_GRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 93, W, 3, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 20)
    c.drawString(50, H - 50, 'Cash Flow Summary')
    c.setFont('Helvetica', 12)
    c.drawString(50, H - 70, client_name + '  |  ' + data.get('report_date', ''))

    rows = [
        ('Monthly Inflow (Take-Home Pay)', fmt(data.get('inflow', 0)), GREEN),
        ('Monthly Outflow (Expenses)', fmt(data.get('outflow', 0)), RED),
        ('Monthly Excess to Private Reserve', fmt(excess), GREEN if excess >= 0 else RED),
        ('', '', None),
        ('Private Reserve — Current Balance', fmt(data.get('private_reserve_balance', 0)), BLUE_RESERVE),
        ('Private Reserve — Target Balance', fmt(data.get('private_reserve_target', 0)), MID_GRAY),
        ('', '', None),
        ('Schwab Investment Portfolio', fmt(inv_bal), NAVY),
    ]

    y = H - 140
    for label, value, color in rows:
        if not label:
            y -= 10
            continue
        c.setFillColor(WHITE)
        c.roundRect(50, y - 28, W - 100, 36, 6, fill=1, stroke=0)
        c.setFillColor(DARK_TEXT)
        c.setFont('Helvetica', 12)
        c.drawString(70, y - 14, label)
        if color:
            c.setFillColor(color)
        c.setFont('Helvetica-Bold', 13)
        c.drawRightString(W - 70, y - 14, value)
        y -= 46

    _draw_footer(c, W, H, 'SACS — Confidential | Windbrook Solutions')
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def draw_tcc_pdf(data):
    """Generate TCC net worth PDF"""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    W, H = letter

    c.setFillColor(LIGHT_GRAY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.rect(0, H - 90, W, 90, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 93, W, 3, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(50, H - 50, 'Total Client Chart')
    c.setFont('Helvetica', 12)
    c.drawString(50, H - 70, 'TCC  |  Net Worth Overview')

    # Client name and date (shifted down to avoid overlap)
    client_name = data.get('client_name', '')
    c.setFont('Helvetica-Bold', 13)
    c.drawRightString(W - 50, H - 62, client_name)
    c.setFont('Helvetica', 11)
    c.drawRightString(W - 50, H - 77, data.get('report_date', ''))

    # Client info bubbles
    y_start = H - 115
    client1 = data.get('client1', {})
    client2 = data.get('client2', {})

    bubble_h = 52
    bubble_w = 200

    def draw_client_bubble(cx, cy, person, color):
        c.setFillColor(color)
        c.setStrokeColor(WHITE)
        c.setLineWidth(2)
        c.roundRect(cx, cy, bubble_w, bubble_h, 8, fill=1, stroke=1)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(cx + bubble_w/2, cy + bubble_h - 17, person.get('name', ''))
        c.setFont('Helvetica', 9)
        c.drawCentredString(cx + bubble_w/2, cy + bubble_h - 31, f"DOB: {person.get('dob', '')}  |  Age {person.get('age', '')}")
        c.setFont('Helvetica', 9)
        c.drawCentredString(cx + bubble_w/2, cy + bubble_h - 44, f"SSN: XXX-XX-{person.get('ssn', '')}")

    draw_client_bubble(50, y_start - bubble_h, client1, NAVY)
    if data.get('is_married') and client2.get('name'):
        draw_client_bubble(W - 50 - bubble_w, y_start - bubble_h, client2, BLUE_RESERVE)

    # Retirement section
    y = y_start - bubble_h - 30
    section_label_y = y

    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(50, section_label_y, 'RETIREMENT ACCOUNTS')
    c.setFillColor(GOLD)
    c.rect(50, section_label_y - 3, 200, 2, fill=1, stroke=0)

    y -= 20
    ret1_accounts = data.get('retirement1_accounts', [])
    ret2_accounts = data.get('retirement2_accounts', [])

    col1_x = 50
    col2_x = W / 2 + 10
    row_h = 52
    acc_w = 230

    def draw_account_bubble(ax, ay, acct, bg_color):
        c.setFillColor(WHITE)
        c.setStrokeColor(bg_color)
        c.setLineWidth(1.5)
        c.roundRect(ax, ay, acc_w, row_h - 4, 6, fill=1, stroke=1)
        c.setFillColor(bg_color)
        c.rect(ax, ay + row_h - 14, acc_w, 14, fill=1, stroke=0)
        c.roundRect(ax, ay + row_h - 18, acc_w, 18, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 9)
        c.drawString(ax + 8, ay + row_h - 10, acct.get('type', ''))
        if acct.get('last4'):
            c.setFont('Helvetica', 8)
            c.drawRightString(ax + acc_w - 8, ay + row_h - 10, f"...{acct.get('last4', '')}")
        c.setFillColor(DARK_TEXT)
        c.setFont('Helvetica-Bold', 14)
        c.drawCentredString(ax + acc_w/2, ay + 12, fmt(acct.get('balance', 0)))
        if acct.get('institution'):
            c.setFillColor(MID_GRAY)
            c.setFont('Helvetica', 7)
            c.drawCentredString(ax + acc_w/2, ay + 3, acct.get('institution', ''))

    # Client 1 retirement
    if ret1_accounts:
        c.setFillColor(MID_GRAY)
        c.setFont('Helvetica', 9)
        c.drawString(col1_x, y, client1.get('name', 'Client 1'))
        y -= 15
        for acct in ret1_accounts:
            draw_account_bubble(col1_x, y - row_h + 4, acct, NAVY)
            y -= row_h

    # Client 2 retirement
    if ret2_accounts and data.get('is_married'):
        y_c2 = section_label_y - 35
        c.setFillColor(MID_GRAY)
        c.setFont('Helvetica', 9)
        c.drawString(col2_x, y_c2, client2.get('name', 'Client 2') if client2 else '')
        y_c2 -= 15
        for acct in ret2_accounts:
            draw_account_bubble(col2_x, y_c2 - row_h + 4, acct, BLUE_RESERVE)
            y_c2 -= row_h

    # Retirement totals summary boxes
    y = min(y, y_start - bubble_h - 20 - (len(ret1_accounts) + 2) * row_h) - 15

    def draw_summary_box(sx, sy, label, value):
        bw = 220
        bh = 44
        c.setFillColor(colors.HexColor('#E8ECF0'))
        c.setStrokeColor(NAVY)
        c.setLineWidth(1)
        c.roundRect(sx, sy, bw, bh, 6, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(sx + bw/2, sy + bh - 14, label)
        c.setFont('Helvetica-Bold', 16)
        c.drawCentredString(sx + bw/2, sy + 10, fmt(value))

    draw_summary_box(50, y, f"{client1.get('name', 'Client 1')} — Retirement Total", data.get('ret1_total', 0))
    if data.get('is_married') and client2.get('name'):
        draw_summary_box(W/2 + 10, y, f"{client2.get('name', 'Client 2')} — Retirement Total", data.get('ret2_total', 0))

    y -= 65

    # Non-retirement
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(50, y, 'NON-RETIREMENT ACCOUNTS')
    c.setFillColor(GOLD)
    c.rect(50, y - 3, 230, 2, fill=1, stroke=0)
    y -= 20

    nr_accounts = data.get('non_retirement_accounts', [])
    nr_x = 50
    for acct in nr_accounts:
        draw_account_bubble(nr_x, y - row_h + 4, acct, colors.HexColor('#4A7C59'))
        nr_x += acc_w + 15
        if nr_x + acc_w > W - 50:
            nr_x = 50
            y -= row_h

    y -= row_h + 5
    draw_summary_box(50, y, 'Non-Retirement Total', data.get('non_ret_total', 0))

    # Trust
    trust_val = data.get('trust_value', 0)
    if trust_val:
        y -= 65
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(50, y, 'TRUST / PROPERTY')
        c.setFillColor(GOLD)
        c.rect(50, y - 3, 160, 2, fill=1, stroke=0)
        y -= 20
        draw_account_bubble(50, y - row_h + 4, {
            'type': 'Primary Residence', 'last4': '',
            'balance': trust_val, 'institution': 'Zillow Zestimate'
        }, colors.HexColor('#7D6608'))
        y -= row_h + 5

    # Grand total
    y -= 15
    gtw = W - 100
    c.setFillColor(NAVY)
    c.roundRect(50, y - 50, gtw, 60, 8, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W/2, y - 5, 'GRAND TOTAL NET WORTH')
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(W/2, y - 38, fmt(data.get('grand_total', 0)))

    # Liabilities
    liabilities = data.get('liabilities', [])
    if liabilities:
        y -= 65
        c.setFillColor(RED)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(50, y, 'LIABILITIES (not deducted from net worth)')
        c.setFillColor(GOLD)
        c.rect(50, y - 3, 280, 2, fill=1, stroke=0)
        y -= 20
        lib_x = 50
        for lib in liabilities:
            draw_account_bubble(lib_x, y - row_h + 4, {
                'type': lib.get('type', ''),
                'last4': '',
                'balance': lib.get('balance', 0),
                'institution': f"{lib.get('rate', '')}% interest rate"
            }, RED)
            lib_x += acc_w + 15
            if lib_x + acc_w > W - 50:
                lib_x = 50
                y -= row_h
        
        y -= row_h + 10
        draw_summary_box(50, y, 'Total Liabilities', data.get('liabilities_total', 0))

    _draw_footer(c, W, H, 'TCC — Confidential | Windbrook Solutions')
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def _draw_arrow(c, x1, y1, x2, y2, color, vertical=False):
    from reportlab.graphics.shapes import Drawing, Polygon
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(3)
    c.line(x1, y1, x2, y2)
    # Arrowhead using path
    p = c.beginPath()
    if vertical:
        p.moveTo(x2 - 8, y2 + 12)
        p.lineTo(x2 + 8, y2 + 12)
        p.lineTo(x2, y2)
        p.close()
    else:
        p.moveTo(x2 - 12, y2 + 8)
        p.lineTo(x2 - 12, y2 - 8)
        p.lineTo(x2, y2)
        p.close()
    c.drawPath(p, fill=1, stroke=0)

def _draw_footer(c, W, H, text):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 30, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.setFont('Helvetica', 8)
    c.drawCentredString(W/2, 10, text)
