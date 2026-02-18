from datetime import date, timedelta

from app.services import erpnext_service


def resolve_period(period: str, from_date: str, to_date: str) -> tuple[str, str]:
    """Convert a period shortcut to (from_date, to_date) ISO strings."""
    today = date.today()
    if period == "today":
        return today.isoformat(), today.isoformat()
    if period == "7d":
        return (today - timedelta(days=6)).isoformat(), today.isoformat()
    if period == "30d":
        return (today - timedelta(days=29)).isoformat(), today.isoformat()
    # custom — caller must provide both dates
    return from_date, to_date


def search_sales(
    period: str,
    from_date: str,
    to_date: str,
    limit: int,
) -> dict:
    """Resolve date range and fetch filtered sales invoices from ERPNext."""
    resolved_from, resolved_to = resolve_period(period, from_date, to_date)
    invoices = erpnext_service.get_sales_data(
        from_date=resolved_from,
        to_date=resolved_to,
        limit=limit,
    )
    return {
        "count": len(invoices),
        "from_date": resolved_from,
        "to_date": resolved_to,
        "invoices": invoices,
    }
