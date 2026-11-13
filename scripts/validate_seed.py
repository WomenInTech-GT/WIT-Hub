#!/usr/bin/env python3
"""Validate WIT-Hub draft JSON for required fields, URLs and past dates.

By default checks data offline. Add --check-links to perform actual HTTP link checks.
HTTP 403, 429, timeouts and network errors mean MANUAL REVIEW, not confirmed broken.
No changes are made to input JSON or any database.
"""
import argparse
import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

FIELDS = ('id', 'title', 'type', 'organizer', 'eligibility', 'url')
ISO = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def valid_url(value):
    if not isinstance(value, str):
        return False
    parsed = urllib.parse.urlparse(value.strip())
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc) and ' ' not in value


def get_date(value):
    if value is None or value == '':
        return None
    if not isinstance(value, str) or not ISO.fullmatch(value):
        raise ValueError('date must use YYYY-MM-DD')
    return date.fromisoformat(value)


def http_status(url, timeout):
    headers = {'User-Agent': 'WIT-Hub-ContentQA/0.1 (student project; link-check)'}
    last = None
    for method in ('HEAD', 'GET'):
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return ('ok', f'HTTP {response.status} ({response.geturl()})')
        except urllib.error.HTTPError as ex:
            last = ex.code
            if method == 'HEAD' and ex.code in (403, 405, 501):
                continue
            if ex.code in (404, 410):
                return ('broken', f'HTTP {ex.code}')
            return ('manual_review', f'HTTP {ex.code}: access may be limited or temporary')
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
            return ('manual_review', f'Connection failed: {type(ex).__name__}')
    return ('manual_review', f'HTTP {last}')


def validate(records, today, check_links, timeout, link_limit):
    issues = []
    by_url = {}
    seen_keys = {}
    checked = 0
    def add(record_id, level, field, code, detail):
        issues.append({'id': record_id, 'level': level, 'field': field, 'code': code, 'detail': detail})
    for item in records:
        rid = str(item.get('id', '<missing id>'))
        for field in FIELDS:
            if not str(item.get(field) or '').strip():
                add(rid, 'error', field, 'missing_required_field', 'Required field is empty')
        key = (str(item.get('title') or '').casefold().strip(), str(item.get('organizer') or '').casefold().strip())
        if key in seen_keys:
            add(rid, 'warning', 'title', 'possible_duplicate', f'Similar title/organizer as {seen_keys[key]}')
        seen_keys[key] = rid
        url = item.get('url')
        if url and not valid_url(url):
            add(rid, 'error', 'url', 'invalid_url_format', f'Not a valid HTTP(S) URL: {url!r}')
        for field in ('event_date', 'event_end_date', 'deadline'):
            try:
                dt = get_date(item.get(field))
            except ValueError as e:
                add(rid, 'error', field, 'invalid_date', str(e))
                continue
            if field == 'deadline' and dt and dt < today:
                add(rid, 'warning', field, 'past_deadline', f'Deadline {dt} is before {today}')
            if field == 'event_end_date' and dt and dt < today:
                add(rid, 'warning', field, 'past_event', f'Event ended {dt}')
            if field == 'event_date' and dt and not item.get('event_end_date') and dt < today:
                add(rid, 'warning', field, 'past_event', f'Event date {dt} is before {today}')
        if not item.get('deadline') and item.get('deadline_raw'):
            add(rid, 'review', 'deadline', 'deadline_unconfirmed', f'Original value: {item["deadline_raw"]}')
        if not item.get('event_date') and item.get('event_date_raw') and item['event_date_raw'] not in ('N/A', 'Not applicable'):
            add(rid, 'review', 'event_date', 'event_date_unconfirmed', f'Original value: {item["event_date_raw"]}')
        if item.get('publication_status') != 'draft_review':
            add(rid, 'warning', 'publication_status', 'unapproved_status', 'Review status must be approved by the team before importing')
        if check_links and valid_url(url):
            if url not in by_url and (link_limit == 0 or checked < link_limit):
                by_url[url] = http_status(url, timeout)
                checked += 1
            if url in by_url:
                status, detail = by_url[url]
                if status == 'broken':
                    add(rid, 'error', 'url', 'broken_link', detail)
                elif status == 'manual_review':
                    add(rid, 'review', 'url', 'link_inconclusive', detail)
    return issues, {'links_tested': checked, 'unique_links_tested': len(by_url), 'link_checks_enabled': check_links}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True)
    parser.add_argument('--report-dir', default='reports')
    parser.add_argument('--check-links', action='store_true', help='Make HTTP requests to inspect link responses')
    parser.add_argument('--link-limit', type=int, default=0, help='Max unique HTTP links; 0 = all (when checking)')
    parser.add_argument('--timeout', type=float, default=8)
    parser.add_argument('--today', default=date.today().isoformat(), help='Override current date (YYYY-MM-DD), for reproducibility')
    args = parser.parse_args()
    payload = json.loads(Path(args.seed).read_text(encoding='utf-8'))
    records = payload.get('opportunities') if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        parser.error('Expected a JSON list or object with opportunities: [...]')
    today = date.fromisoformat(args.today)
    issues, network = validate(records, today, args.check_links, args.timeout, args.link_limit)
    out = Path(args.report_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out/'validation_issues.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id','level','field','code','detail'])
        writer.writeheader()
        writer.writerows(issues)
    summary = {
        'checked_on': str(today),
        'records': len(records),
        'issues_by_level': dict(Counter(x['level'] for x in issues)),
        'issues_by_code': dict(Counter(x['code'] for x in issues)),
        'http_link_checks': network,
        'disclaimer': 'Not an approval to publish/import. All data is in draft review; HTTP checks do not confirm URL content matches opportunity.'
    }
    (out/'validation_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print('Reports: ' + str(out/'validation_issues.csv') + ', ' + str(out/'validation_summary.json'))

if __name__ == '__main__':
    main()
