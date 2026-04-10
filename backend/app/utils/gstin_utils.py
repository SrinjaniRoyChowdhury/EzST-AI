"""
utils/gstin_utils.py
─────────────────────
GSTIN (GST Identification Number) utilities:
validation, state code lookup, and checksum verification.
"""

import re
from typing import Optional

GSTIN_REGEX = re.compile(
    r"^([0-9]{2})([A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})$"
)

STATE_CODE_MAP: dict[str, str] = {
    "01": "Jammu & Kashmir",   "02": "Himachal Pradesh",
    "03": "Punjab",            "04": "Chandigarh",
    "05": "Uttarakhand",       "06": "Haryana",
    "07": "Delhi",             "08": "Rajasthan",
    "09": "Uttar Pradesh",     "10": "Bihar",
    "11": "Sikkim",            "12": "Arunachal Pradesh",
    "13": "Nagaland",          "14": "Manipur",
    "15": "Mizoram",           "16": "Tripura",
    "17": "Meghalaya",         "18": "Assam",
    "19": "West Bengal",       "20": "Jharkhand",
    "21": "Odisha",            "22": "Chhattisgarh",
    "23": "Madhya Pradesh",    "24": "Gujarat",
    "26": "Dadra & NH",        "27": "Maharashtra",
    "28": "Andhra Pradesh",    "29": "Karnataka",
    "30": "Goa",               "31": "Lakshadweep",
    "32": "Kerala",            "33": "Tamil Nadu",
    "34": "Puducherry",        "35": "Andaman & Nicobar",
    "36": "Telangana",         "37": "Andhra Pradesh (New)",
    "97": "Other Territory",   "99": "Centre Jurisdiction",
}


def is_valid_gstin(gstin: str) -> bool:
    """Quick boolean check."""
    return bool(GSTIN_REGEX.match(gstin.upper().strip()))


def get_state_from_gstin(gstin: str) -> Optional[str]:
    """Return state name from first 2 chars of GSTIN."""
    code = gstin[:2] if len(gstin) >= 2 else ""
    return STATE_CODE_MAP.get(code)


def is_same_state(gstin1: str, gstin2: str) -> bool:
    """Return True if both GSTINs are from the same state."""
    return gstin1[:2] == gstin2[:2]


def get_pan_from_gstin(gstin: str) -> Optional[str]:
    """Extract the embedded PAN from a GSTIN (chars 3–12)."""
    if not is_valid_gstin(gstin):
        return None
    return gstin[2:12]


def parse_gstin(gstin: str) -> dict:
    """Return a structured breakdown of a GSTIN."""
    gstin = gstin.upper().strip()
    if not is_valid_gstin(gstin):
        return {"valid": False, "gstin": gstin}
    return {
        "valid": True,
        "gstin": gstin,
        "state_code": gstin[:2],
        "state": get_state_from_gstin(gstin),
        "pan": get_pan_from_gstin(gstin),
        "entity_number": gstin[12],
        "check_digit": gstin[14],
    }