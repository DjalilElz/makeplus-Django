"""
Bulk participant import: builds an event-specific Excel template (its
actual form fields + whichever blocs/items/workshops it has enabled),
parses+validates an uploaded copy into a ParticipantImportBatch for
review, and processes the resulting rows through the exact same
registration pipeline as the event owner's "Nouvelle inscription"
manual-entry feature (dashboard.views_event_owner.event_owner_new_registration)
-- an imported participant ends up identical to a manually-entered one:
same badge/access, same pricing/discount math, same searchability.
"""
import re
import unicodedata
from functools import lru_cache

from django.db import transaction
from django.utils import timezone

from events.form_validation_service import create_participant_for_event, get_or_create_user_for_manual_registration
from .blocs_service import compute_order
from .models_blocs import BlocItem
from .models_import import ParticipantImportBatch, ParticipantImportRow
from .views_blocs import get_public_bloc_context

STATUS_HEADER = 'Bloc: Statut *'
RESTAURATION_HEADER = 'Bloc: Restauration'
SOCIAL_EVENT_HEADER = 'Bloc: Événement social'
WORKSHOPS_HEADER = 'Ateliers (workshops)'

# On the live public form these render as a fixed <select>/radio
# group/checkbox group bound to the field's own 'options' list -- a
# submission can never carry anything else. The import must enforce the
# same thing (see _validate_row) instead of accepting arbitrary text.
SELECT_LIKE_FIELD_TYPES = {'select', 'radio', 'checkbox'}

# Can't be filled from a spreadsheet cell at all, so it's left out of
# the template entirely rather than offered as a column that can never
# actually be used.
NOT_IMPORTABLE_FIELD_TYPES = {'file'}


def build_import_columns(event):
    """
    The ordered list of columns this event's template/import actually
    needs: one per configured form field (minus any NOT_IMPORTABLE_FIELD_TYPES),
    then one per bloc that's both enabled AND has at least one real item
    to choose from (mirrors get_public_bloc_context's own filtering
    exactly, so the import never offers a bloc the public form itself
    wouldn't).

    Returns {'form_fields': [...], 'bloc_columns': [...], 'bloc_context': dict or None}.
    form_fields entries carry 'options' (the field's own choices, for
    select/radio/checkbox) so they can be validated and listed in the
    template's legend sheet exactly like bloc columns are.
    bloc_columns entries: {'header', 'bloc_key' ('status'/'restauration'/
    'social_event'/'workshops'), 'required', 'select_mode', 'valid_values': [names]}.
    """
    form_config = event.custom_forms.first()
    form_fields = []
    if form_config:
        for field in form_config.fields_config:
            if field.get('type') in NOT_IMPORTABLE_FIELD_TYPES:
                continue
            form_fields.append({
                'name': field.get('name'),
                'label': field.get('label') or field.get('name'),
                'type': field.get('type', 'text'),
                'required': bool(field.get('required')),
                'options': field.get('options') or [],
            })

    bloc_context = get_public_bloc_context(event, include_inactive=False)
    bloc_columns = []
    if bloc_context:
        header_by_key = {
            'status': STATUS_HEADER,
            'restauration': RESTAURATION_HEADER,
            'social_event': SOCIAL_EVENT_HEADER,
        }
        for bloc in bloc_context['custom_blocs']:
            bloc_columns.append({
                'header': header_by_key[bloc['key']],
                'bloc_key': bloc['key'],
                'required': bloc['key'] == 'status',
                'select_mode': bloc['select_mode'],
                'valid_values': [item.name for item in bloc['items']],
            })
        if bloc_context['paid_sessions']:
            bloc_columns.append({
                'header': WORKSHOPS_HEADER,
                'bloc_key': 'workshops',
                'required': False,
                'select_mode': 'multiple',
                'valid_values': [s.title for s in bloc_context['paid_sessions']],
            })

    return {'form_fields': form_fields, 'bloc_columns': bloc_columns, 'bloc_context': bloc_context}


def generate_import_template_workbook(event):
    """Returns an openpyxl Workbook: an 'Import' sheet with headers (+ a sample
    row), and a 'Valeurs valides' sheet listing every bloc/workshop column's
    exact accepted values -- so whoever fills the sheet can copy-paste
    the right spelling instead of guessing."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    columns = build_import_columns(event)
    wb = Workbook()

    ws = wb.active
    ws.title = 'Import'
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='2D1B6B')

    headers = [f['label'] + (' *' if f['required'] else '') for f in columns['form_fields']]
    headers += [c['header'] for c in columns['bloc_columns']]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        ws.column_dimensions[cell.column_letter].width = max(18, len(header) + 2)

    # One example row so the expected shape (comma-separated multi-values,
    # exact names) is obvious without needing the legend sheet open.
    example = []
    for f in columns['form_fields']:
        if f['type'] == 'email':
            example.append('jean.dupont@example.com')
        elif f['name'] in ('first_name', 'prenom'):
            example.append('Jean')
        elif f['name'] in ('last_name', 'nom'):
            example.append('Dupont')
        elif f['type'] in SELECT_LIKE_FIELD_TYPES and f['options']:
            example.append(', '.join(f['options'][:2]) if f['type'] == 'checkbox' else f['options'][0])
        else:
            example.append('')
    for c in columns['bloc_columns']:
        if not c['valid_values']:
            example.append('')
        elif c['select_mode'] == 'multiple':
            example.append(', '.join(c['valid_values'][:2]))
        else:
            example.append(c['valid_values'][0])
    ws.append(example)

    select_like_fields = [f for f in columns['form_fields'] if f['type'] in SELECT_LIKE_FIELD_TYPES and f['options']]
    if columns['bloc_columns'] or select_like_fields:
        legend = wb.create_sheet('Valeurs valides')
        legend.append(['Colonne', 'Valeurs acceptées (orthographe exacte)'])
        legend['A1'].font = Font(bold=True)
        legend['B1'].font = Font(bold=True)
        for f in select_like_fields:
            note = (
                'Une ou plusieurs valeurs, séparées par des virgules (ou ;)' if f['type'] == 'checkbox'
                else 'Une seule valeur'
            )
            legend.append([f['label'], note])
            for value in f['options']:
                legend.append(['', value])
        for c in columns['bloc_columns']:
            note = (
                'Une seule valeur' if c['select_mode'] == 'single'
                else 'Une ou plusieurs valeurs, séparées par des virgules (ou ;)'
            )
            legend.append([c['header'], note])
            for value in c['valid_values']:
                legend.append(['', value])
        legend.column_dimensions['A'].width = 30
        legend.column_dimensions['B'].width = 50

    return wb


# Characters that look alike but differ byte-for-byte between what a
# form-builder option was typed with and what Excel produces -- each was
# a real cause of rejected rows (SARM 2026: "Medecine d'urgence" vs the
# option's "d’urgence", "13 - Tlemcen" vs the option's "13 – Tlemcen").
_LOOKALIKES = str.maketrans({
    # apostrophes: right/left single quote, modifier letter, grave, acute
    **dict.fromkeys(('\u2019', '\u2018', '\u02bc', '\u0060', '\u00b4'), "'"),
    # dashes: en, em, non-breaking hyphen, minus sign, hyphen
    **dict.fromkeys(('\u2013', '\u2014', '\u2011', '\u2212', '\u2010'), '-'),
    # non-breaking spaces
    **dict.fromkeys(('\u00a0', '\u202f'), ' '),
})
# Several values in one cell may be separated by any of these.
_SEPARATORS_RE = re.compile(r'([,;\n])')


@lru_cache(maxsize=8192)
def _normalize(text):
    """Comparison key: case, accents, look-alike apostrophes/dashes and
    spacing don't count -- "Médecine d’urgence" == "medecine d'urgence"."""
    text = unicodedata.normalize('NFKD', str(text).translate(_LOOKALIKES))
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(text.lower().split())


def _find_option(piece, valid_values):
    """The option `piece` designates, in the option's own spelling, or
    None. Tolerant (see _normalize), plus a final "s" is optional
    ("Autres" -> "Autre") -- but only when that leaves exactly ONE
    candidate, so two genuinely different options are never merged."""
    key = _normalize(piece)
    if not key:
        return None
    for value in valid_values:
        if _normalize(value) == key:
            return value
    singular = _without_final_s(key)
    candidates = [v for v in valid_values if _without_final_s(_normalize(v)) == singular]
    return candidates[0] if len(candidates) == 1 else None


def _without_final_s(key):
    return key[:-1] if key.endswith('s') else key


def _match_names(raw_value, valid_values, allow_multiple):
    """
    Matches a cell's raw text against valid_values (see _find_option for
    how tolerant that is). Returns (matched_values: list, unmatched: list)
    -- matched_values are always valid_values' own canonical spelling,
    never the user's raw typed text.

    allow_multiple: the cell may hold several values separated by
    commas (or ; / line breaks). Option names can themselves contain
    commas (a workshop titled "Le Kiné, pilote de l'extubation : ...,
    gestes et suites..."), so the cell isn't blindly split: at each
    position the LONGEST run of pieces that forms a known option wins,
    and a piece only stands alone when nothing longer matches.
    """
    if raw_value is None or not str(raw_value).strip():
        return [], []
    text = str(raw_value).strip()
    if not allow_multiple:
        option = _find_option(text, valid_values)
        return ([option], []) if option else ([], [text])

    # ['A', ',', ' B, part 2'...]: pieces at even indexes, separators at odd.
    parts = _SEPARATORS_RE.split(text)
    pieces, seps = parts[0::2], parts[1::2]
    matched, unmatched, pending = [], [], []
    i = 0
    while i < len(pieces):
        found = None
        for j in range(len(pieces), i, -1):
            candidate = ''.join(pieces[k] + (seps[k] if k < j - 1 else '') for k in range(i, j))
            found = _find_option(candidate, valid_values)
            if found:
                break
        if found:
            if pending:
                unmatched.append(', '.join(pending))
                pending = []
            if found not in matched:
                matched.append(found)
            i = j
        else:
            # Unrecognised pieces next to each other are reported as one
            # value, so the message shows what was typed, not fragments.
            if pieces[i].strip():
                pending.append(pieces[i].strip())
            i += 1
    if pending:
        unmatched.append(', '.join(pending))
    return matched, unmatched


def parse_uploaded_workbook(uploaded_file):
    """Reads the first sheet's header row + data rows into a list of
    {header: raw_cell_value} dicts, 1:1 with build_import_columns'
    headers. Blank trailing rows are skipped."""
    from openpyxl import load_workbook

    wb = load_workbook(uploaded_file, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows_iter = ws.iter_rows(values_only=True)
    header_row = next(rows_iter, None)
    if not header_row:
        return []

    headers = [str(h).strip() if h is not None else '' for h in header_row]
    parsed = []
    for raw_row in rows_iter:
        if raw_row is None or all(cell is None or str(cell).strip() == '' for cell in raw_row):
            continue
        row_dict = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            row_dict[header] = raw_row[idx] if idx < len(raw_row) else None
        parsed.append(row_dict)
    return parsed


def _validate_row(event, columns, row_dict, registered_emails):
    """
    Returns a dict ready to become a ParticipantImportRow's fields
    (email, full_name, form_data, resolved_item_ids, resolved_session_ids,
    status, error_message). Never raises -- an unexpected problem with
    one row becomes status='error' with a message, not a crash that
    takes the rest of the file down with it.

    registered_emails: lowercased set of every email already registered
    for this event, computed ONCE by the caller -- doing that lookup as
    a per-row query here instead was a real production incident: a large
    file meant hundreds of synchronous round-trips to the database
    inside one request, long enough to hit gunicorn's worker timeout and
    get killed mid-request (visible in the logs as a SystemExit from
    gunicorn's own abort handler, not a normal exception).
    """
    errors = []
    form_data = {}
    email = ''

    for field in columns['form_fields']:
        header = field['label'] + (' *' if field['required'] else '')
        raw_value = row_dict.get(header, '')

        if field['type'] in SELECT_LIKE_FIELD_TYPES and field['options']:
            # Must match the live form exactly: a select/radio/checkbox
            # field there can never submit anything outside its own
            # options, so neither can an import (same strict matching
            # already used for bloc columns below).
            allow_multiple = field['type'] == 'checkbox'
            matched, unmatched = _match_names(raw_value, field['options'], allow_multiple)
            if unmatched:
                errors.append(
                    f"« {field['label']} » : valeur(s) non reconnue(s) : {', '.join(unmatched)}. "
                    f"Valeurs acceptées : {', '.join(field['options'])}."
                )
            if not allow_multiple and len(matched) > 1:
                errors.append(f"« {field['label']} » n'accepte qu'une seule valeur.")
            if field['required'] and not matched:
                errors.append(f"« {field['label']} » est requis.")
            value = matched if allow_multiple else (matched[0] if matched else '')
        else:
            value = '' if raw_value is None else str(raw_value).strip()
            if field['required'] and not value:
                errors.append(f"« {field['label']} » est requis.")

        form_data[field['name']] = value
        if field['type'] == 'email' or field['name'] in ('email',):
            email = (value or '').lower()

    if not email:
        errors.append("E-mail manquant ou invalide.")

    first_name = form_data.get('first_name') or form_data.get('prenom') or ''
    last_name = form_data.get('last_name') or form_data.get('nom') or ''
    full_name = f"{first_name} {last_name}".strip()

    resolved_item_ids = []
    resolved_session_ids = []
    for col in columns['bloc_columns']:
        raw_value = row_dict.get(col['header'], '')
        allow_multiple = col['select_mode'] == 'multiple'
        matched, unmatched = _match_names(raw_value, col['valid_values'], allow_multiple)

        if col['required'] and not matched:
            errors.append(f"« {col['header']} » est requis et doit correspondre exactement à une valeur de la feuille « Valeurs valides ».")
        if unmatched:
            errors.append(f"« {col['header']} » : valeur(s) non reconnue(s) : {', '.join(unmatched)}.")
        if not allow_multiple and len(matched) > 1:
            errors.append(f"« {col['header']} » n'accepte qu'une seule valeur.")

        if col['bloc_key'] == 'workshops':
            sessions_by_name = {s.title: s for s in columns['bloc_context']['paid_sessions']}
            resolved_session_ids.extend(str(sessions_by_name[name].id) for name in matched if name in sessions_by_name)
        else:
            items_by_name = {
                item.name: item for b in columns['bloc_context']['custom_blocs'] if b['key'] == col['bloc_key']
                for item in b['items']
            }
            resolved_item_ids.extend(str(items_by_name[name].id) for name in matched if name in items_by_name)

    if email and not errors:
        if email in registered_emails:
            return {
                'email': email, 'full_name': full_name, 'form_data': form_data,
                'resolved_item_ids': resolved_item_ids, 'resolved_session_ids': resolved_session_ids,
                'status': 'skipped_duplicate', 'error_message': "Déjà inscrit à cet événement -- ignoré.",
            }

    return {
        'email': email, 'full_name': full_name, 'form_data': form_data,
        'resolved_item_ids': resolved_item_ids, 'resolved_session_ids': resolved_session_ids,
        'status': 'error' if errors else 'valid',
        'error_message': ' '.join(errors),
    }


def create_import_batch(event, user, uploaded_file):
    """Parses + validates the uploaded file and persists a
    ParticipantImportBatch with one ParticipantImportRow per data row,
    ready for the admin to review before anything is actually created."""
    from events.models import ParticipantEventRegistration

    columns = build_import_columns(event)
    parsed_rows = parse_uploaded_workbook(uploaded_file)

    # One query for the whole file instead of one per row -- see
    # _validate_row's docstring for why that used to time out on a
    # large file.
    registered_emails = {
        email.lower() for email in ParticipantEventRegistration.objects.filter(
            event=event
        ).values_list('participant__user__email', flat=True) if email
    }

    batch = ParticipantImportBatch.objects.create(
        event=event, uploaded_by=user,
        original_filename=getattr(uploaded_file, 'name', '')[:255],
        status='ready',
    )

    rows = []
    for row_number, row_dict in enumerate(parsed_rows, start=2):  # row 1 is the header
        validated = _validate_row(event, columns, row_dict, registered_emails)
        rows.append(ParticipantImportRow(
            batch=batch, row_number=row_number, raw_data={k: ('' if v is None else str(v)) for k, v in row_dict.items()},
            **validated,
        ))
    ParticipantImportRow.objects.bulk_create(rows)

    return batch


def process_import_row(row, event, config, bloc_context, form_config):
    """
    Creates the real registration for one 'valid' row -- same pipeline
    as event_owner_new_registration: passwordless user, Participant +
    ParticipantEventRegistration, a FormSubmission capturing the raw
    form answers, and (only if this event has blocs at all) a
    RegistrationOrder priced through compute_order exactly like a real
    submission, left at its default 'pending' (unpaid/"Registered")
    status -- never auto-marked paid just because it came from a file.
    Mutates row.status/error_message/participant; caller saves it.

    form_config is passed in (looked up once per request by the caller)
    rather than queried here -- it's the same row every time for a given
    event, so re-querying it per row was a wasted query multiplied across
    the whole batch.

    Deliberately does NOT send the registration-confirmation email --
    that happens afterward, in its own separate batch phase (see
    send_pending_confirmation_emails below), so a slow/variable network
    call per row can never block or time out row creation itself (it
    did: this is pure DB work and was fast, batched at 10/request,
    until an earlier version sent the email inline here too and most
    batches started exceeding gunicorn's worker timeout).
    """
    from .models_form import FormSubmission

    try:
        with transaction.atomic():
            first_name = row.form_data.get('first_name') or row.form_data.get('prenom') or ''
            last_name = row.form_data.get('last_name') or row.form_data.get('nom') or ''

            user = get_or_create_user_for_manual_registration(row.email, first_name, last_name)
            participant = create_participant_for_event(user, event)

            submission = None
            if form_config:
                submission = FormSubmission.objects.create(
                    form=form_config, data=row.form_data, email=row.email,
                )

            if bloc_context:
                result = compute_order(
                    event=event, config=config,
                    selected_item_ids=row.resolved_item_ids, selected_session_ids=row.resolved_session_ids,
                    on_date=timezone.now().date(),
                )
                from .models_blocs import RegistrationOrder
                RegistrationOrder.objects.create(
                    event=event, form_submission=submission, participant=participant,
                    period_id=result['active_period_id'], full_name=row.full_name, email=row.email,
                    items_snapshot=result['snapshot'], subtotals=result['subtotals'],
                    distinct_blocs_count=result['distinct_blocs_count'],
                    total_before_reduction=result['total_before_reduction'],
                    period_discount_percent=result['period_discount_percent'],
                    blocs_discount_percent=result['blocs_discount_percent'],
                    total_discount_percent=result['total_discount_percent'],
                    total_after_reduction=result['total_after_reduction'],
                    receipt_file='',  # bulk-imported rows never carry an upload receipt
                )

            row.status = 'created'
            row.participant = participant
            row.error_message = ''
    except Exception as e:
        row.status = 'error'
        row.error_message = f"Erreur lors de la création : {e}"


def send_pending_confirmation_emails(batch, limit):
    """
    Sends the registration-confirmation email (with QR code -- same one
    a self-registering participant gets) for up to `limit` rows in this
    batch that were successfully created but not yet emailed, then marks
    them sent. Deliberately a separate phase/endpoint from row creation
    -- see process_import_row's docstring for why mixing the two caused
    most creation batches to exceed gunicorn's worker timeout.

    Idempotent and safe to call repeatedly: a row is only ever picked up
    while confirmation_email_sent=False, so a request that itself times
    out mid-batch just leaves the remaining rows to be picked up by the
    next call -- never a duplicate email, never a lost one.

    Returns the number of emails actually sent in this call -- 0 means
    every row it tried failed, so the caller should stop rather than
    retry the same rows forever (they stay unsent, for the
    send_import_confirmation_emails command to pick up later).
    """
    import logging
    from events.form_validation_service import send_registration_confirmation_email_sync

    rows = list(
        batch.rows.filter(status='created', confirmation_email_sent=False)
        .select_related('participant__user')
        .order_by('row_number')[:limit]
    )
    sent = 0
    for row in rows:
        if row.participant and row.participant.user:
            # Sent in this request (it's already its own small batch), so a
            # row is only marked sent once the email actually went out -- it
            # used to be handed to a background thread and marked sent
            # immediately, whatever happened to the email afterwards.
            success, error = send_registration_confirmation_email_sync(row.participant.user, batch.event)
            if not success:
                logging.getLogger(__name__).error("Import confirmation email to %s not sent: %s", row.email, error)
                continue
        row.confirmation_email_sent = True
        row.save(update_fields=['confirmation_email_sent'])
        sent += 1
    return sent
