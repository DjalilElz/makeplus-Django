from django import template

register = template.Library()


@register.filter
def spaced(amount):
    """1250000 -> '1 250 000' (centimes, with a comma, only when there are some).
    Same format as the Rapport de caisse PDF, whatever the server locale."""
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        return amount
    if amount == int(amount):
        return f"{int(amount):,}".replace(',', ' ')
    return f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
