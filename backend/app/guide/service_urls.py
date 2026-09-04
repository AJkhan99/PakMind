"""Service URL registry — known government website URLs for direct scraping.

When the database doesn't have enough information, we go directly to the
official government website instead of relying only on generic web search.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Known government service pages, organized by service name.
# Each entry has: url, title, and optional province tags.
# These are real, publicly accessible URLs from Pakistani government sites.
# ---------------------------------------------------------------------------

SERVICE_URLS: dict[str, list[dict[str, Any]]] = {
    "passport": [
        {"url": "https://www.dgip.gov.pk/passport-category/passport-new/", "title": "DGIP — New Passport Application", "province": None},
        {"url": "https://www.dgip.gov.pk/passport-category/passport-renewal/", "title": "DGIP — Passport Renewal", "province": None},
        {"url": "https://www.dgip.gov.pk/", "title": "DGIP — Directorate General of Immigration & Passports", "province": None},
        {"url": "https://onlinemrp.dgip.gov.pk/", "title": "DGIP Online Passport Portal", "province": None},
    ],
    "cnic": [
        {"url": "https://www.nadra.gov.pk/citizen-registration/", "title": "NADRA — Citizen Registration (CNIC)", "province": None},
        {"url": "https://www.nadra.gov.pk/", "title": "NADRA — National Database & Registration Authority", "province": None},
        {"url": "https://id.nadra.gov.pk/", "title": "Pak Identity — Online CNIC Services", "province": None},
    ],
    "nicop": [
        {"url": "https://www.nadra.gov.pk/nicop/", "title": "NADRA — NICOP (Overseas Pakistanis)", "province": None},
        {"url": "https://id.nadra.gov.pk/", "title": "Pak Identity — Online Services", "province": None},
    ],
    "driving_licence": [
        {"url": "https://excise.punjab.gov.pk/driving-license/", "title": "Punjab Excise — Driving Licence", "province": "Punjab"},
        {"url": "https://excise.punjab.gov.pk/", "title": "Punjab Excise & Taxation Department", "province": "Punjab"},
        {"url": "https://dls.gos.pk/", "title": "Sindh Driving Licence Services", "province": "Sindh"},
    ],
    "vehicle_registration": [
        {"url": "https://excise.punjab.gov.pk/motor-registration/", "title": "Punjab Excise — Vehicle Registration", "province": "Punjab"},
        {"url": "https://excise.punjab.gov.pk/", "title": "Punjab Excise & Taxation Department", "province": "Punjab"},
    ],
    "domicile": [
        {"url": "https://dcrawalpindi.punjab.gov.pk/domicile-certificate", "title": "DC Rawalpindi — Domicile Certificate", "province": "Punjab"},
    ],
    "birth_certificate": [
        {"url": "https://www.nadra.gov.pk/birth-registration/", "title": "NADRA — Birth Registration", "province": None},
    ],
    "death_certificate": [
        {"url": "https://www.nadra.gov.pk/death-registration/", "title": "NADRA — Death Registration", "province": None},
        {"url": "https://www.nadra.gov.pk/", "title": "NADRA — National Database & Registration Authority", "province": None},
    ],
    "marriage_certificate": [
        {"url": "https://islamabad.gov.pk/", "title": "ICT Administration — Marriage Registration", "province": "ICT"},
    ],
    "police_character_certificate": [
        {"url": "https://www.punjabpolice.gov.pk/", "title": "Punjab Police — Character Certificate", "province": "Punjab"},
        {"url": "https://khidmatmarkaz.punjabpolice.gov.pk/", "title": "Punjab Police Khidmat Markaz", "province": "Punjab"},
    ],
    "tax_return": [
        {"url": "https://www.fbr.gov.pk/", "title": "FBR — Federal Board of Revenue", "province": None},
        {"url": "https://e.fbr.gov.pk/", "title": "FBR Iris — Online Tax Filing", "province": None},
    ],
    "ntn": [
        {"url": "https://www.fbr.gov.pk/", "title": "FBR — NTN Registration", "province": None},
        {"url": "https://e.fbr.gov.pk/", "title": "FBR Iris — Tax Registration", "province": None},
    ],
    "arms_licence": [
        {"url": "https://www.moipp.gov.pk/", "title": "Ministry of Interior — Arms Licence", "province": None},
    ],
    "property_mutation": [
        {"url": "https://excise.punjab.gov.pk/", "title": "Punjab Excise — Property Mutation (Inteqal)", "province": "Punjab"},
    ],
    "b_form": [
        {"url": "https://www.nadra.gov.pk/citizen-registration/", "title": "NADRA — B-Form (Child Registration)", "province": None},
        {"url": "https://id.nadra.gov.pk/", "title": "Pak Identity — Online Services", "province": None},
    ],
    "electricity_connection": [
        {"url": "https://www.lesco.gov.pk/", "title": "LESCO — New Electricity Connection (Lahore)", "province": "Punjab"},
        {"url": "https://www.iesco.gov.pk/", "title": "IESCO — New Electricity Connection (Islamabad)", "province": "ICT"},
    ],
    "gas_connection": [
        {"url": "https://www.sngpl.com.pk/", "title": "SNGPL — Sui Northern Gas (Punjab/KPK)", "province": "Punjab"},
        {"url": "https://www.ssgc.com.pk/", "title": "SSGC — Sui Southern Gas (Sindh/Balochistan)", "province": "Sindh"},
    ],
    "pension": [
        {"url": "https://www.agp.gov.pk/", "title": "Accountant General of Pakistan — Pension", "province": None},
    ],
}

# ---------------------------------------------------------------------------
# Common search queries for deep scraping (used when service is unknown)
# ---------------------------------------------------------------------------

GOV_SEARCH_QUERIES = {
    "default": "{service} {province} Pakistan government requirements procedure fee",
    "requirements": "{service} required documents {province} Pakistan government",
    "fee": "{service} fee charges cost {province} Pakistan government 2026",
    "steps": "{service} application procedure steps {province} Pakistan government",
    "location": "{service} office center {city} {province} Pakistan address",
}


def get_urls_for_service(
    service: str | None,
    province: str | None = None,
    max_urls: int = 3,
) -> list[dict[str, Any]]:
    """Get known government URLs for a service, filtered by province.

    Returns URLs most relevant to the query, preferring:
    1. Province-specific pages (if province is provided)
    2. General/federal pages
    3. Homepage URLs
    """
    if not service:
        return []

    # Normalize service name
    service_key = service.lower().replace(" ", "_").replace("-", "_")

    urls = SERVICE_URLS.get(service_key, [])
    if not urls:
        # Try partial match
        for key, key_urls in SERVICE_URLS.items():
            if service_key in key or key in service_key:
                urls = key_urls
                break

    if not urls:
        return []

    # Sort: province-specific first (if province matches), then general
    def sort_priority(entry: dict) -> int:
        entry_province = entry.get("province")
        if province and entry_province and province.lower() in entry_province.lower():
            return 0  # Province match — highest priority
        if entry_province is None:
            return 1  # General/federal — second priority
        return 2  # Wrong province — lowest priority

    urls = sorted(urls, key=sort_priority)
    return urls[:max_urls]


def get_search_query(
    service: str | None,
    province: str | None = None,
    city: str | None = None,
    intent: str | None = None,
) -> str:
    """Build a targeted search query for deep web scraping."""
    template = GOV_SEARCH_QUERIES.get(intent or "default", GOV_SEARCH_QUERIES["default"])
    return template.format(
        service=service or "government service",
        province=province or "Pakistan",
        city=city or "",
    ).strip()
