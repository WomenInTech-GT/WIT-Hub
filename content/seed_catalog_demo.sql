-- Fictional examples and search fixtures for 002_content_catalog.sql.
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
-- Additional fictional fixtures: deliberately varied wording and competing matches.
-- These demo IDs are refreshed on rerun so relative-date checks stay useful.
INSERT INTO catalog.content_items (
    id, title, description, url, category, tags,
    location_mode, location, starts_at, ends_at, deadline_at,
    content_kind, organization, source, last_updated, eligibility_status, schedule_precision, timezone, deadline_status, deadline_timezone
)
SELECT id, title, description, 'https://example.org/demo/' || id, kind, tags,
       mode, venue, begins, begins + INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '60 days',
       CASE WHEN kind IN ('event', 'workshop', 'conference') THEN 'event'
            WHEN kind IN ('program', 'mentorship') THEN 'program' ELSE 'opportunity' END,
       'Demo organization', 'Fictional demonstration catalog', CURRENT_DATE,
       'unrestricted', 'time', 'America/New_York', 'fixed', 'America/New_York'
FROM (VALUES
 ('demo-expanded-cs', 'DEMO: Computer science internship', 'Build software with a mentor.', 'internship', ARRAY['coding'], 'online', 'Remote', TIMESTAMPTZ '2027-07-01 10:00:00-04'),
 ('demo-expanded-ai', 'DEMO: Artificial intelligence projects', 'An introductory classification project.', 'project', ARRAY['coding','artificial intelligence'], 'online', 'Zoom', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-robotics-body', 'DEMO: Engineering lab placement', 'Explore robotics.', 'research', ARRAY['engineering'], 'in-person', 'Atlanta', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-robotics-title', 'DEMO: Robotics', 'Build a robot.', 'project', ARRAY['coding'], 'online', 'Zoom', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-resume', 'DEMO: Resume review event', 'Practice communicating your experience.', 'event', ARRAY['careers'], 'online', 'Zoom', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-scholarship', 'DEMO: Scholarships for women', 'Fictional tuition support.', 'scholarship', ARRAY['funding'], 'online', 'Online', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-data-program', 'DEMO: Part-time data science program', 'A fictional part-time learning program.', 'program', ARRAY['data science'], 'online', 'Zoom', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-pm', 'DEMO: PM mentorship', 'Product management mentorship; PM is explicitly defined here.', 'mentorship', ARRAY['product management'], 'online', 'Zoom', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-aerospace', 'DEMO: Paid aerospace research', 'Fictional paid research placement.', 'research', ARRAY['aerospace'], 'in-person', 'Atlanta', TIMESTAMPTZ '2027-07-01 10:00:00-04'),
 ('demo-competition', 'DEMO: Engineering competitions', 'A fictional design competition.', 'competition', ARRAY['engineering'], 'in-person', 'Atlanta', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-grad', 'DEMO: New grad opportunities', 'A fictional graduate recruiting event.', 'event', ARRAY['careers'], 'online', 'Zoom', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-job', 'DEMO: Remote jobs', 'A fictional graduate software job.', 'job', ARRAY['coding'], 'online', 'Remote', TIMESTAMPTZ '2027-07-01 10:00:00-04'),
 ('demo-workshop', 'DEMO: In-person engineering workshops', 'An introductory engineering workshop.', 'workshop', ARRAY['engineering'], 'in-person', 'Atlanta', CURRENT_TIMESTAMP + INTERVAL '20 days'),
 ('demo-conference', 'DEMO: Computer science conferences', 'Research talks.', 'conference', ARRAY['computer science'], 'in-person', 'Atlanta', (date_trunc('year', CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York') + INTERVAL '10 months 10 days 10 hours') AT TIME ZONE 'America/New_York'),
 ('demo-wit-next-week', 'DEMO: Women in Tech events', 'Meet students on campus.', 'event', ARRAY['community'], 'in-person', 'Campus, Atlanta', (date_trunc('week', CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York') + INTERVAL '8 days 10 hours') AT TIME ZONE 'America/New_York'),
 ('demo-campus-weekend', 'DEMO: Campus events', 'Meet students.', 'event', ARRAY['community'], 'in-person', 'Campus, Atlanta', (date_trunc('week', CURRENT_TIMESTAMP AT TIME ZONE 'America/New_York') + INTERVAL '5 days 14 hours') AT TIME ZONE 'America/New_York')
) AS fixture(id, title, description, kind, tags, mode, venue, begins)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    tags = EXCLUDED.tags, category = EXCLUDED.category,
    location_mode = EXCLUDED.location_mode, location = EXCLUDED.location,
    starts_at = EXCLUDED.starts_at, ends_at = EXCLUDED.ends_at,
    deadline_at = EXCLUDED.deadline_at;

COMMIT;
