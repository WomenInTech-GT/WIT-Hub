#!/usr/bin/env python3
"""Convert WIT-Hub Google Sheets CSV exports to provisional JSON seeds.

Python standard library only. DO NOT import to staging until the backend schema is approved.
"""
import argparse
import csv
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATE_RANGE = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(?:to|–|—)\s+(\d{4}-\d{2}-\d{2})$')


def clean(value):
    return str(value or '').strip()


def optional(value):
    s = clean(value)
    return s if s else None


def iso_or_none(value):
    s = clean(value)
    if not DATE.fullmatch(s):
        return None
    try:
        date.fromisoformat(s)
        return s
    except ValueError:
        return None


def parse_event_date(value):
    text = clean(value)
    if iso_or_none(text):
        return text, None
    match = DATE_RANGE.fullmatch(text)
    if match and iso_or_none(match.group(1)) and iso_or_none(match.group(2)):
        return match.group(1), match.group(2)
    return None, None


def yn(value):
    val = clean(value).lower()
    return True if val == 'yes' else False if val == 'no' else None


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        # Allow the full Google Sheets CSV with title rows above the header.
        rows = csv.reader(f)
        for row in rows:
            if row and clean(row[0]) in ('ID', 'Project ID'):
                headers = [clean(x) for x in row]
                break
        else:
            raise ValueError(f'Could not find table header in {path}')
        for pos, row in enumerate(rows, start=1):
            if not row or not any(clean(x) for x in row):
                continue
            padded = list(row) + [''] * max(0, len(headers) - len(row))
            item = dict(zip(headers, padded))
            if not clean(item.get(headers[0])):
                continue
            yield item


def opportunities_from_csv(path):
    output = []
    for item in read_csv(path):
        start, end = parse_event_date(item.get('Event Date'))
        raw_deadline = clean(item.get('Application Deadline'))
        output.append({
            'id': clean(item.get('ID')),
            'title': clean(item.get('Opportunity / Event')),
            'type': clean(item.get('Category')),
            'organizer': clean(item.get('Organizer')),
            'eligibility': clean(item.get("Who It's For (undergraduate)")),
            'event_date': start,
            'event_end_date': end,
            'event_date_raw': clean(item.get('Event Date')) or None,
            'deadline': iso_or_none(raw_deadline),
            'deadline_raw': raw_deadline or None,
            'url': clean(item.get('Official Source URL')),
            'availability': optional(item.get('Availability / Next Action')),
            'topics': [t.strip() for t in clean(item.get('Topics')).split(';') if t.strip()],
            'women_focused': yn(item.get('Women-Focused?')),
            'robotics_hardware': yn(item.get('Robotics / Hardware?')),
            'eligibility_review': optional(item.get('Eligibility / Review')),
            'source_reviewed': optional(item.get('Source Reviewed')),
            'publication_status': 'draft_review',
            'original_publication_status': optional(item.get('Publication Status')),
            'editorial_notes': optional(item.get('Important Notes')),
        })
    return output


def projects_from_csv(path):
    result = []
    for item in read_csv(path):
        result.append({
            'id': clean(item.get('Project ID')),
            'title': clean(item.get('Project Title')),
            'year': int(item['Year']) if clean(item.get('Year')).isdigit() else None,
            'type': clean(item.get('Category')),
            'team': clean(item.get('Team')),
            'summary': clean(item.get('One-Line Summary')),
            'problem': optional(item.get('Problem')),
            'solution': optional(item.get('Solution / Student Work')),
            'technologies': [t.strip() for t in clean(item.get('Technologies')).split(';') if t.strip()],
            'url': clean(item.get('Official Source')),
            'publication_permission': 'unconfirmed',
            'publication_status': 'draft_review',
        })
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--opportunities', required=True, help='Google Sheets Opportunities tab exported as CSV')
    p.add_argument('--projects', help='Student Projects tab exported as CSV')
    p.add_argument('--output-dir', default='content/seed')
    args = p.parse_args()
    dest = Path(args.output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    meta = {
        'schema_status': 'DRAFT — NOT APPROVED',
        'exported_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'warning': 'Do not import into staging until final schema mapping, eligibility and editorial approval.',
    }
    records = opportunities_from_csv(args.opportunities)
    (dest/'opportunities.draft.json').write_text(json.dumps({'meta': meta, 'opportunities': records}, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f'Exported {len(records)} opportunities')
    if args.projects:
        projects = projects_from_csv(args.projects)
        (dest/'student_projects.draft.json').write_text(json.dumps({'meta': meta, 'projects': projects}, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        print(f'Exported {len(projects)} projects')

if __name__ == '__main__':
    main()
