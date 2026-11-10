-- Fictional examples for 002_content_catalog.sql; independent of legacy seed_demo.sql.
-- Fixed dates keep the examples reproducible. These are not live listings.
BEGIN;
INSERT INTO catalog.content_items (
    id, content_kind, category, title, description, organization, url, source,
    last_updated, tags, eligibility_status, eligibility, eligible_majors,
    location_mode, schedule_precision, start_date, end_date, starts_at, ends_at,
    timezone, deadline_status, deadline_date, deadline_timezone
) VALUES
(
    'catalog-demo-internship', 'opportunity', 'internship', 'DEMO: Software internship',
    'Fictional summer internship for computer science students.', 'Demo employer',
    'https://example.org/demo/internship', 'Fictional demonstration catalog',
    DATE '2026-11-09', ARRAY['coding'], 'restricted', ARRAY['Computer science majors'],
    ARRAY['computer science'], 'online', 'date', DATE '2027-06-01', DATE '2027-08-01',
    NULL, NULL, 'America/New_York', 'fixed', DATE '2027-03-01', 'America/New_York'
),
(
    'catalog-demo-workshop', 'event', 'workshop', 'DEMO: Robotics workshop',
    'Fictional one-off workshop open to everyone.', 'Demo student organization',
    'https://example.org/demo/workshop', 'Fictional demonstration catalog',
    DATE '2026-11-09', ARRAY['robotics'], 'unrestricted', '{}', '{}',
    'online', 'time', NULL, NULL,
    TIMESTAMPTZ '2027-02-10 15:00:00-05', TIMESTAMPTZ '2027-02-10 17:00:00-05',
    'America/New_York', 'none', NULL, NULL
),
(
    'catalog-demo-mentorship', 'program', 'mentorship', 'DEMO: Mentorship program',
    'Fictional ongoing program with rolling applications; eligibility is not yet verified.',
    'Demo mentors', 'https://example.org/demo/mentorship', 'Fictional demonstration catalog',
    DATE '2026-11-09', ARRAY['careers'], 'unknown', '{}', '{}',
    'hybrid', 'unknown', NULL, NULL, NULL, NULL, NULL, 'rolling', NULL, NULL
),
(
    'catalog-demo-guide', 'resource', 'guide', 'DEMO: Resume guide',
    'Fictional reference material with no schedule or application deadline.', NULL,
    'https://example.org/demo/guide', 'Fictional demonstration catalog',
    DATE '2026-11-09', ARRAY['careers', 'resume'], 'unrestricted', '{}', '{}',
    'not-applicable', 'not-applicable', NULL, NULL, NULL, NULL, NULL, 'none', NULL, NULL
)
ON CONFLICT (id) DO NOTHING;
COMMIT;
