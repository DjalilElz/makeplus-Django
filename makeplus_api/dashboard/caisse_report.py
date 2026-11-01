"""
"Rapport de caisse" PDF -- MakePlus-branded report of completed caisse
payments: summary by payment mode, transactions per caisse, and every
payment line. Built from the same payment_breakdown() as the caisse screen
and the stats page, so its figures always match them.

Used by the stats page's PDF export (whole event, or the filtered period /
caisse) and by each caisse's own "Rapport de remise de caisse".
"""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.db.models import Count, Sum
from django.utils import timezone

# Agency block printed in the header.
AGENCY_LINES = [
    'Agence Événementielle',
    'Cité Gué de Constantine, Alger',
    'Email : contact@wemakeplus.com',
    'Tél : 0559 48 62 89',
]

# Platform colours (logo purple, dashboard violet) and neutrals.
PURPLE = '#872C7A'
VIOLET = '#2D1B6B'
INK = '#1D1A24'
MUTED = '#6B6475'
LINE = '#E7E2DC'
PANEL = '#F7F3F8'
TILE_HIGHLIGHT = '#F3E8F1'

# Badge colours per payment mode: (text, background, border).
BADGES = {
    'cash': ('#17663A', '#E6F4EC', '#9FD2B3'),
    'bank_transfer': (VIOLET, '#ECE8F6', '#B9AEE0'),
    'sponsoring': (PURPLE, '#F6E8F3', '#DDB0D3'),
    'mixed': ('#5B5B66', '#EFEFF2', '#C9C9D1'),
}

LOGO_PATH = Path(__file__).resolve().parent / 'static' / 'dashboard' / 'images' / 'makeplus-logo-report.png'

FRENCH_MONTHS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
                 'septembre', 'octobre', 'novembre', 'décembre']


def _dzd(amount):
    """1250000 -> '1 250 000 DZD' (centimes only when there are some)."""
    amount = amount or 0
    if amount == int(amount):
        text = f"{int(amount):,}".replace(',', ' ')
    else:
        text = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
    return f"{text} DZD"


def _french_date(dt):
    return f"{dt.day} {FRENCH_MONTHS[dt.month - 1]} {dt.year}"


def build_caisse_report(event, transactions, edited_by, scope_lines=None):
    """
    Returns the PDF as bytes.

    transactions: CaisseTransaction queryset already narrowed to what the
    report covers (event, and optionally one caisse / a period); only the
    completed ones are reported. edited_by: who produced it (a user's name,
    or the caisse's name). scope_lines: optional extra header lines, e.g.
    the period or caisse filter in effect.
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from caisse.services import payment_breakdown

    completed = transactions.filter(status='completed')
    totals = payment_breakdown(completed)
    per_caisse = list(
        completed.order_by().values('caisse__id', 'caisse__name')
        .annotate(count=Count('id'), amount=Sum('total_amount')).order_by('caisse__name')
    )
    lines = list(completed.select_related('caisse', 'participant__user', 'sponsor').order_by('created_at'))

    c = colors.HexColor
    left_margin = right_margin = 16 * mm
    page_width, page_height = A4
    usable = page_width - left_margin - right_margin

    def style(name, **kw):
        base = dict(fontName='Helvetica', fontSize=9, leading=12, textColor=c(INK))
        base.update(kw)
        return ParagraphStyle(name, **base)

    s_agency_bold = style('agency_bold', fontName='Helvetica-Bold', textColor=c(MUTED))
    s_agency = style('agency', textColor=c(MUTED))
    s_title = style('title', fontName='Helvetica-Bold', fontSize=19, leading=23, alignment=TA_RIGHT, textColor=c(VIOLET))
    s_meta = style('meta', fontSize=9.5, leading=13, alignment=TA_RIGHT)
    s_section = style('section', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c(VIOLET))
    s_h2 = style('h2', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=c(INK))
    s_tile_label = style('tile_label', fontSize=7.5, leading=10, alignment=TA_CENTER, textColor=c(MUTED))
    s_tile_value = style('tile_value', fontName='Helvetica-Bold', fontSize=13, leading=16, alignment=TA_CENTER)
    s_tile_main = style('tile_main', fontName='Helvetica-Bold', fontSize=14.5, leading=18, alignment=TA_CENTER, textColor=c(PURPLE))
    s_cell = style('cell', fontSize=8.5, leading=11)
    s_cell_muted = style('cell_muted', fontSize=7.5, leading=10, textColor=c(MUTED))
    s_cell_right = style('cell_right', fontSize=8.5, leading=11, alignment=TA_RIGHT)
    s_cell_bold_right = style('cell_bold_right', fontName='Helvetica-Bold', fontSize=8.5, leading=11, alignment=TA_RIGHT)
    s_head = style('head', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white)
    s_head_right = style('head_right', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white, alignment=TA_RIGHT)
    s_note = style('note', fontSize=8, leading=11, textColor=c(MUTED))
    s_empty = style('empty', fontSize=9, leading=12, textColor=c(MUTED), alignment=TA_CENTER)

    now = timezone.localtime()
    story = []

    # ---- Header: logo + agency (left), title + event/edition (right) ----
    logo = Image(str(LOGO_PATH), width=52 * mm, height=52 * mm * 308 / 1494)
    left = [logo, Spacer(1, 4 * mm), Paragraph(escape(AGENCY_LINES[0]), s_agency_bold)]
    left += [Paragraph(escape(line), s_agency) for line in AGENCY_LINES[1:]]
    right = [
        Paragraph('RAPPORT DE CAISSE', s_title),
        Spacer(1, 2 * mm),
        Paragraph(f'Événement : <font color="{PURPLE}"><b>{escape(event.name)}</b></font>', s_meta),
        Paragraph(f"Date d'édition : {_french_date(now)} à {now:%H:%M}", s_meta),
        Paragraph(f'Édité par : {escape(edited_by)}', s_meta),
    ]
    right += [Paragraph(escape(line), s_meta) for line in (scope_lines or [])]
    header = Table([[left, right]], colWidths=[usable * 0.48, usable * 0.52])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, 0), 2, c(PURPLE)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5 * mm),
    ]))
    story += [header, Spacer(1, 7 * mm)]

    # ---- Résumé financier: total + one tile per payment mode ----
    tile_w = (usable - 10 * mm) / 4
    tiles = [
        ('MONTANT GLOBAL', totals['total']['amount'], True),
        ('TOTAL ESPÈCES', totals['cash']['amount'], False),
        ('TOTAL VIREMENT BANCAIRE', totals['bank_transfer']['amount'], False),
        ('TOTAL PRISE EN CHARGE', totals['sponsoring']['amount'], False),
    ]
    tile_cells = [[Paragraph(label, s_tile_label), Spacer(1, 1.5 * mm),
                   Paragraph(_dzd(amount), s_tile_main if main else s_tile_value)] for label, amount, main in tiles]
    tiles_table = Table([tile_cells], colWidths=[tile_w] * 4, rowHeights=[20 * mm])
    tiles_style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (0, 0), 1, c(PURPLE)), ('BACKGROUND', (0, 0), (0, 0), c(TILE_HIGHLIGHT)),
        ('BACKGROUND', (1, 0), (-1, 0), colors.white),
    ]
    for col in range(1, 4):
        tiles_style.append(('BOX', (col, 0), (col, 0), 0.6, c(LINE)))
    tiles_table.setStyle(TableStyle(tiles_style))

    summary = [Paragraph('RÉSUMÉ FINANCIER', s_section), Spacer(1, 3 * mm), tiles_table]
    if totals['sponsors'] or totals['other']['count']:
        parts = [f"{escape(row['name'])} : <b>{_dzd(row['amount'])}</b>" for row in totals['sponsors']]
        note = ('Prise en charge par organisme — ' + ' · '.join(parts)) if parts else ''
        if totals['other']['count']:
            note += (' — ' if note else '') + f"Paiements mixtes (anciens) : <b>{_dzd(totals['other']['amount'])}</b>"
        summary += [Spacer(1, 2.5 * mm), Paragraph(note, s_note)]

    # Transactions per caisse
    caisse_rows = [[Paragraph('Caisse', s_head), Paragraph('Transactions', s_head_right), Paragraph('Montant', s_head_right)]]
    for row in per_caisse:
        caisse_rows.append([
            Paragraph(f"{escape(row['caisse__name'])} <font color='{MUTED}'>(C-{row['caisse__id']:03d})</font>", s_cell),
            Paragraph(str(row['count']), s_cell_right),
            Paragraph(_dzd(row['amount']), s_cell_right),
        ])
    caisse_rows.append([
        Paragraph('<b>Total</b>', s_cell), Paragraph(f"<b>{totals['total']['count']}</b>", s_cell_right),
        Paragraph(f"<b>{_dzd(totals['total']['amount'])}</b>", s_cell_right),
    ])
    caisse_table = Table(caisse_rows, colWidths=[usable * 0.5 - 8 * mm, usable * 0.2, usable * 0.3], repeatRows=1)
    caisse_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c(VIOLET)),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, c('#FBF9FC')]),
        ('BACKGROUND', (0, -1), (-1, -1), c(TILE_HIGHLIGHT)),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, c(LINE)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    summary += [Spacer(1, 5 * mm), Paragraph('<b>Nombre de transactions par caisse</b>', s_cell), Spacer(1, 2 * mm), caisse_table]

    panel = Table([[summary]], colWidths=[usable])
    panel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c(PANEL)),
        ('BOX', (0, 0), (-1, -1), 0.6, c(LINE)),
        # cap 0 (butt): the accent bar stops exactly at the panel's edges
        ('LINEBEFORE', (0, 0), (0, -1), 3, c(PURPLE), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 5 * mm), ('RIGHTPADDING', (0, 0), (-1, -1), 5 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5 * mm), ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
    ]))
    story += [panel, Spacer(1, 8 * mm)]

    # ---- Détail des encaissements ----
    story += [Paragraph('Détail des encaissements', s_h2), Spacer(1, 3 * mm)]
    widths = [usable * 0.17, usable * 0.25, usable * 0.20, usable * 0.23, usable * 0.15]

    def badge(txn):
        label = txn.payment_display
        if txn.payment_method == 'sponsoring' and txn.sponsor_id:
            label = f'Prise en charge ({txn.sponsor.name})'
        fg, bg, border = BADGES.get(txn.payment_method, BADGES['mixed'])
        max_w = widths[3] - 10
        text_w = min(stringWidth(label, 'Helvetica-Bold', 7.5) + 10, max_w)
        cell = Table([[Paragraph(f'<b>{escape(label)}</b>', style('badge', fontSize=7.5, leading=9.5, textColor=c(fg)))]],
                     colWidths=[text_w])
        cell.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c(bg)), ('BOX', (0, 0), (-1, -1), 0.6, c(border)),
            ('ROUNDEDCORNERS', [3, 3, 3, 3]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        cell.hAlign = 'LEFT'
        return cell

    detail = [[Paragraph(h, s_head) for h in ('Caisse / ID', 'Participant', "Date d'encaissement", 'Mode de règlement')]
              + [Paragraph('Montant', s_head_right)]]
    for txn in lines:
        user = txn.participant.user
        name = user.get_full_name().strip() or user.username
        detail.append([
            Paragraph(f"{escape(txn.caisse.name)}<br/><font size='7' color='{MUTED}'>C-{txn.caisse_id:03d}</font>", s_cell),
            Paragraph(f"{escape(name)}<br/><font size='7' color='{MUTED}'>{escape(user.email or '')}</font>", s_cell),
            Paragraph(timezone.localtime(txn.created_at).strftime('%d/%m/%Y - %H:%M'), s_cell),
            badge(txn),
            Paragraph(_dzd(txn.total_amount), s_cell_bold_right),
        ])
    if not lines:
        detail.append([Paragraph('Aucun encaissement pour cette sélection.', s_empty), '', '', '', ''])
    detail_table = Table(detail, colWidths=widths, repeatRows=1)
    detail_style = [
        ('BACKGROUND', (0, 0), (-1, 0), c(VIOLET)),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c('#FBF9FC')]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, c(LINE)),
        ('BOX', (0, 0), (-1, -1), 0.6, c(LINE)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    if not lines:
        detail_style.append(('SPAN', (0, 1), (-1, 1)))
    detail_table.setStyle(TableStyle(detail_style))
    story.append(detail_table)

    # ---- Footer on every page, with "Page X sur Y" ----
    class NumberedCanvas(pdf_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._pages = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                self._footer(total)
                super().showPage()
            super().save()

        def _footer(self, total):
            y = 10 * mm
            self.setStrokeColor(c(LINE))
            self.setLineWidth(0.6)
            self.line(left_margin, y + 4.5 * mm, page_width - right_margin, y + 4.5 * mm)
            self.setFont('Helvetica', 7.5)
            self.setFillColor(c(MUTED))
            self.drawString(left_margin, y, 'Rapport de caisse — MakePlus Agence Événementielle  ·  Généré depuis la plateforme de gestion')
            self.drawRightString(page_width - right_margin, y, f'Page {self._pageNumber} sur {total}')

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=left_margin, rightMargin=right_margin,
        topMargin=14 * mm, bottomMargin=20 * mm,
        title=f'Rapport de caisse — {event.name}', author='MakePlus',
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
