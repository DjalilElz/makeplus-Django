"""
Spreadsheet (Excel/CSV) import for e-mail campaigns.

Each column becomes a {{variable}} named after its header (lower-case,
accents removed, spaces -> underscores: "Spécialité" -> {{specialite}}),
and each row a potential recipient. The rows are stored on the campaign;
the admin then picks which of them to send to.
"""
import csv
import io
import re
import unicodedata
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

MAX_ROWS = 20000


class SheetError(Exception):
    pass


def column_key(label):
    text = unicodedata.normalize('NFKD', str(label)).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9]+', '_', text.lower()).strip('_')
    return text or 'colonne'


def _cell_text(value):
    if value is None:
        return ''
    if isinstance(value, datetime):
        if value.hour or value.minute or value.second:
            return value.strftime('%d/%m/%Y %H:%M')
        return value.strftime('%d/%m/%Y')
    if isinstance(value, date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _read_table(upload):
    name = (upload.name or '').lower()
    raw = upload.read()
    if name.endswith('.csv'):
        for encoding in ('utf-8-sig', 'cp1252'):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise SheetError("Impossible de lire ce fichier CSV (encodage inconnu).")
        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        return list(csv.reader(io.StringIO(text), dialect))

    if name.endswith(('.xlsx', '.xlsm')):
        from openpyxl import load_workbook
        try:
            wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        except Exception:
            raise SheetError("Impossible de lire ce fichier Excel.")
        ws = wb.worksheets[0]
        return [list(row) for row in ws.iter_rows(values_only=True)]

    raise SheetError("Format non pris en charge : utilisez un fichier .xlsx ou .csv.")


def guess_email_column(columns, rows):
    for col in columns:
        if 'mail' in col['key']:
            return col['key']
    # No "e-mail" header: the column whose values look most like e-mails.
    best, best_hits = '', 0
    for col in columns:
        hits = sum(1 for r in rows[:50] if '@' in r.get(col['key'], ''))
        if hits > best_hits:
            best, best_hits = col['key'], hits
    return best


def parse_sheet(upload):
    """
    Returns (columns, rows, email_column): columns as [{"key", "label"}],
    rows as dicts keyed by column key (all values as text), fully empty
    rows dropped. Raises SheetError with a French message.
    """
    table = _read_table(upload)
    # First non-empty row is the header.
    while table and not any(_cell_text(c) for c in table[0]):
        table.pop(0)
    if not table:
        raise SheetError("Le fichier est vide.")

    header = [_cell_text(c) for c in table[0]]
    columns, used = [], set()
    for index, label in enumerate(header):
        if not label:
            continue
        key = base = column_key(label)
        n = 2
        while key in used:
            key = f'{base}_{n}'
            n += 1
        used.add(key)
        columns.append({'key': key, 'label': label, 'index': index})
    if not columns:
        raise SheetError("La première ligne doit contenir les noms des colonnes.")

    rows = []
    for raw_row in table[1:]:
        row = {}
        for col in columns:
            i = col['index']
            row[col['key']] = _cell_text(raw_row[i]) if i < len(raw_row) else ''
        if any(row.values()):
            rows.append(row)
        if len(rows) > MAX_ROWS:
            raise SheetError(f"Le fichier dépasse {MAX_ROWS} lignes.")

    columns = [{'key': c['key'], 'label': c['label']} for c in columns]
    return columns, rows, guess_email_column(columns, rows)


def row_email(row, email_column):
    """The row's e-mail, lower-cased, or '' if missing/invalid."""
    email = (row.get(email_column) or '').strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return ''
    return email


_FIRST_NAME_KEYS = ('prenom', 'first_name', 'firstname')
_LAST_NAME_KEYS = ('nom', 'last_name', 'lastname', 'nom_de_famille')
_FULL_NAME_KEYS = ('nom_complet', 'nom_et_prenom', 'nom_prenom', 'full_name', 'name')


def row_name(row):
    first = next((row[k] for k in _FIRST_NAME_KEYS if row.get(k)), '')
    last = next((row[k] for k in _LAST_NAME_KEYS if row.get(k)), '')
    if first or last:
        return f'{first} {last}'.strip()
    return next((row[k] for k in _FULL_NAME_KEYS if row.get(k)), '')


def row_variables(row):
    """
    The row as template variables. Besides one variable per column,
    {{first_name}}/{{last_name}}/{{name}} are filled from the usual name
    columns when the sheet has them, so the standard variables work too.
    """
    variables = dict(row)
    first = next((row[k] for k in _FIRST_NAME_KEYS if row.get(k)), '')
    last = next((row[k] for k in _LAST_NAME_KEYS if row.get(k)), '')
    if first:
        variables.setdefault('first_name', first)
    if last:
        variables.setdefault('last_name', last)
    name = row_name(row)
    if name:
        variables.setdefault('name', name)
    return variables
