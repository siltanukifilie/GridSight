"""Audience labels for the local MVP, not an authentication/authorization layer."""

WORKSPACES = {
    "developer": "Mini-grid developer",
    "investor": "Investor / lender",
}


def workspace(role="developer"):
    if not isinstance(role, str) or role not in WORKSPACES:
        raise ValueError("Role must be developer or investor (investor includes lenders).")
    return {"role": role, "label": WORKSPACES[role], "access_control": False}
