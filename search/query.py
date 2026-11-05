"""Small, auditable query vocabulary; no LLM or guessed eligibility."""
import calendar
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Ambiguous PM is deliberately not expanded (product/project/program management).
ALIASES = {
    "cs": "computer science", "ai": "artificial intelligence",
    "ml": "machine learning", "wit": "women in tech",
}
# Curated corrections avoid silently rewriting unfamiliar names or acronyms.
CORRECTIONS = {"internshps": "internships", "internsip": "internship",
               "scholorships": "scholarships", "hackaton": "hackathon"}


@dataclass
class QueryPlan:
    groups: list[str]
    notes: list[str] = field(default_factory=list)
    start: datetime | None = None
    end: datetime | None = None

    def as_dict(self):
        return {"lexical_groups": self.groups, "notes": self.notes,
                "starts_at_from": self.start.isoformat() if self.start else None,
                "starts_at_before": self.end.isoformat() if self.end else None}


def interpret_query(query: str, now: datetime, timezone_name: str = "America/New_York",
                    enabled: bool = True) -> QueryPlan:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must include a timezone")
    text = query.strip()
    # Preserve explicit websearch syntax in its entirety, including quoted dates.
    if not enabled or re.search(r'"|\bOR\b|(?:^|\s)-\S', text, re.I):
        return QueryPlan([text] if text else [])
    plan = QueryPlan([])
    local = now.astimezone(ZoneInfo(timezone_name))
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    relative = re.search(r"\b(next week|this weekend|today|tomorrow)\b", text, re.I)
    months = "|".join(calendar.month_name[1:])
    absolute = re.search(rf"\b(summer|{months})(?:\s+(20\d{{2}}))?\b|\b(20\d{{2}})\b", text, re.I)
    match = relative or absolute
    if relative:
        phrase = relative.group().lower()
        if phrase == "next week":
            plan.start = midnight + timedelta(days=7 - midnight.weekday())
            plan.end = plan.start + timedelta(days=7)
        elif phrase == "this weekend":
            plan.start = midnight + timedelta(days=5 - midnight.weekday())
            plan.end = plan.start + timedelta(days=2)
        else:
            plan.start = midnight + timedelta(days=int(phrase == "tomorrow"))
            plan.end = plan.start + timedelta(days=1)
    elif absolute:
        season, year, standalone = absolute.groups()
        year = int(year or standalone or local.year)
        month = 6 if season and season.lower() == "summer" else next(
            (i for i, name in enumerate(calendar.month_name) if season and name.lower() == season.lower()), 1)
        end_month = 9 if season and season.lower() == "summer" else (month + 1 if season else 13)
        plan.start = midnight.replace(year=year, month=month, day=1)
        plan.end = plan.start.replace(year=year + int(end_month == 13), month=1 if end_month == 13 else end_month)
    if match:
        text = text[:match.start()] + " " + text[match.end():]
        plan.notes.append(f"{match.group()} interpreted as a start-date window in {timezone_name}")
        text = re.sub(r"\bhappening\b", "", text, flags=re.I)
    for token in re.findall(r"[\w]+(?:-[\w]+)*", text.lower()):
        if match and token in {"in", "on", "for", "during", "the", "this"}:
            continue
        corrected = CORRECTIONS.get(token, token)
        if corrected != token:
            plan.notes.append(f"Corrected {token} to {corrected}")
        if corrected in ALIASES:
            expansion = ALIASES[corrected]
            plan.groups.append(f'{corrected} OR "{expansion}"')
            plan.notes.append(f"Expanded {corrected} to {expansion}")
        else:
            plan.groups.append(corrected)
    # Punctuation-only input must not accidentally become a browse request.
    if not plan.groups and query.strip() and not match:
        plan.groups = [query.strip()]
    return plan
