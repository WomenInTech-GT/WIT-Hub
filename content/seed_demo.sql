BEGIN;

INSERT INTO opportunities (
    id,
    title,
    description,
    source_url,
    opportunity_type,
    eligible_majors,
    eligible_years,
    experience_levels,
    tags,
    location_mode,
    location_name,
    starts_at,
    ends_at,
    application_deadline
)
VALUES
(
    'demo-freshman',
    'DEMO: Freshman opportunities in technology',
    'An introductory event for first-year students exploring technical projects.',
    'https://example.org/demo/freshman',
    'event',
    ARRAY[]::text[],
    ARRAY[1],
    ARRAY['beginner'],
    ARRAY['technology', 'coding'],
    'in-person',
    'Demo campus room, Atlanta',
    CURRENT_TIMESTAMP + INTERVAL '14 days',
    CURRENT_TIMESTAMP + INTERVAL '14 days 2 hours',
    CURRENT_TIMESTAMP + INTERVAL '7 days'
),
(
    'demo-cs-internship',
    'DEMO: CS internships summer 2027',
    'A fictional computer science internship involving web development.',
    'https://example.org/demo/cs-internship',
    'internship',
    ARRAY['computer science'],
    ARRAY[1, 2, 3, 4],
    ARRAY[]::text[],
    ARRAY['coding', 'web development', 'cs'],
    'online',
    'Remote',
    '2027-06-01T09:00:00-04:00',
    '2027-08-01T17:00:00-04:00',
    '2027-03-01T23:59:00-05:00'
),
(
    'demo-hackathon',
    'DEMO: Beginner-friendly hackathon',
    'Build a small coding project with a student team.',
    'https://example.org/demo/hackathon',
    'hackathon',
    ARRAY[]::text[],
    ARRAY[]::integer[],
    ARRAY['beginner'],
    ARRAY['coding', 'teamwork'],
    'in-person',
    'Demo innovation center, Atlanta',
    CURRENT_TIMESTAMP + INTERVAL '21 days',
    CURRENT_TIMESTAMP + INTERVAL '22 days',
    CURRENT_TIMESTAMP + INTERVAL '14 days'
),
(
    'demo-ai-project',
    'DEMO: AI projects and machine learning projects',
    'An introductory project exploring classification and model evaluation.',
    'https://example.org/demo/ai-project',
    'project',
    ARRAY[]::text[],
    ARRAY[]::integer[],
    ARRAY['beginner', 'intermediate'],
    ARRAY['ai', 'machine learning', 'coding'],
    'online',
    'Zoom',
    CURRENT_TIMESTAMP + INTERVAL '14 days',
    CURRENT_TIMESTAMP + INTERVAL '42 days',
    CURRENT_TIMESTAMP + INTERVAL '10 days'
),
(
    'demo-robotics',
    'DEMO: Mechanical engineering research in robotics',
    'Explore robot design and mechanical engineering research methods.',
    'https://example.org/demo/robotics',
    'research',
    ARRAY['mechanical engineering'],
    ARRAY[2, 3, 4],
    ARRAY['intermediate'],
    ARRAY['robotics', 'mechanical engineering'],
    'in-person',
    'Demo engineering lab, Atlanta',
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    CURRENT_TIMESTAMP + INTERVAL '90 days',
    CURRENT_TIMESTAMP + INTERVAL '20 days'
),
(
    'demo-expired',
    'DEMO: Expired robotics workshop',
    'An intentionally expired opportunity for testing deadline exclusion.',
    'https://example.org/demo/expired',
    'workshop',
    ARRAY[]::text[],
    ARRAY[]::integer[],
    ARRAY[]::text[],
    ARRAY['robotics'],
    'online',
    'Zoom',
    CURRENT_TIMESTAMP + INTERVAL '7 days',
    CURRENT_TIMESTAMP + INTERVAL '7 days 2 hours',
    CURRENT_TIMESTAMP - INTERVAL '1 day'
)
ON CONFLICT (id) DO NOTHING;

-- Additional fictional fixtures: deliberately varied wording and competing matches.
-- These demo IDs are refreshed on rerun so relative-date checks stay useful.
INSERT INTO opportunities (
    id, title, description, source_url, opportunity_type, tags,
    location_mode, location_name, starts_at, ends_at, application_deadline
)
SELECT id, title, description, 'https://example.org/demo/' || id, kind, tags,
       mode, venue, begins, begins + INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '60 days'
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
    tags = EXCLUDED.tags, opportunity_type = EXCLUDED.opportunity_type,
    location_mode = EXCLUDED.location_mode, location_name = EXCLUDED.location_name,
    starts_at = EXCLUDED.starts_at, ends_at = EXCLUDED.ends_at,
    application_deadline = EXCLUDED.application_deadline;

COMMIT;
