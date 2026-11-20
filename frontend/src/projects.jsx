import React, { lazy, Suspense, useState } from 'react';
import BlankListings from './BlankListings.jsx';

const DraftProjects = import.meta.env.DEV
  ? lazy(async () => {
    const { default: seed } = await import('../../content/seed/student_projects.draft.json');
    return { default: () => <ProjectsPreview projects={seed.projects} /> };
  })
  : null;

function ProjectCard({ project }) {
  return (
    <article className="listing project-info-card">
      <div className="listing-body">
        <div className="listing-top">
          <span className="tag">{project.type}</span>
        </div>
        <h3>{project.title}</h3>
        <p>{project.summary}</p>
        <ul className="project-facts">
          {project.technologies.map(technology => <li key={technology}>{technology}</li>)}
        </ul>
        {/^https?:\/\//i.test(project.url) && (
          <a className="project-source" href={project.url}>View project source ↗</a>
        )}
        <details className="listing-bottom">
          <summary className="text-button">
            Learn more: <span className="project-details-arrow" aria-hidden="true">↓</span>
          </summary>
          <p><strong>Year</strong> · {project.year}</p>
          <p><strong>Team</strong> · {project.team}</p>
          <p><strong>Problem</strong> · {project.problem}</p>
          <p><strong>Solution</strong> · {project.solution}</p>
        </details>
      </div>
    </article>
  );
}

function ProjectsPreview({ projects }) {
  const [query, setQuery] = useState('');
  const keyword = query.trim().toLowerCase();
  const matches = projects.filter(project =>
    [project.title, project.type, project.summary, ...project.technologies]
      .some(value => value.toLowerCase().includes(keyword))
  );

  return (
    <main className="container career-main">
      <section className="career-intro">
        <div>
          <h1>Student Projects</h1>
          <p>Explore what Georgia Tech students are building and the problems they set out to solve.</p>
        </div>
      </section>
      <section className="library" aria-labelledby="project-list-heading">
        <div className="section-heading">
          <div>
            <h2 id="project-list-heading">Explore projects</h2>
            <p className="library-count" role="status">{matches.length} of {projects.length} projects</p>
          </div>
        </div>
        <div className="search-row">
          <label className="resource-search">
            <input
              type="search"
              placeholder="Search projects or technologies"
              aria-label="Search projects"
              value={query}
              onChange={event => setQuery(event.target.value)}
            />
          </label>
        </div>
        <div className="listing-grid projects">
          {matches.map(project => <ProjectCard key={project.id} project={project} />)}
        </div>
        {matches.length === 0 && <p id="empty">No projects match your search.</p>}
      </section>
    </main>
  );
}

export default function Page() {
  if (DraftProjects) {
    return <Suspense fallback={<p role="status">Loading projects…</p>}><DraftProjects /></Suspense>;
  }

  return (<>
<main className="container career-main"><section className="career-intro"><div><h1>Projects</h1><p>Explore hands-on briefs with a purpose. Build a new skill, find a collaborator, and turn an idea into something you can proudly share.</p></div><aside className="matches"><strong>✧</strong><h3>Project briefs</h3><p>Go beyond watching and reading. Every brief includes a clear challenge and practical steps.</p></aside></section><section className="featured blank-feature" aria-label="Featured content placeholder"><div className="blank-image" aria-hidden="true"></div><div aria-hidden="true"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div><div className="blank-meta"></div><div className="blank-button"></div></div></section><section className="library"><div className="section-heading"><div><h2>Small projects. Skills that stay with you.</h2><p className="library-count">Build your next portfolio piece. Start anytime. Free to use.</p></div><label className="sort">Sort by: <select id="sort" aria-label="Sort listings" disabled><option value="recommended">Recommended</option><option value="title">Title A–Z</option></select></label></div><div className="search-row"><label className="resource-search"><span aria-hidden="true">⌕</span><input id="search" type="search" placeholder="Search projects, skills, or keywords…" aria-label="Search projects" disabled /></label><select data-filter="0" aria-label="Difficulty" disabled><option value="all">Difficulty</option></select><select data-filter="1" aria-label="Duration" disabled><option value="all">Duration</option></select><select data-filter="2" aria-label="Solo / team" disabled><option value="all">Solo / team</option></select></div><div className="category-tabs" role="group" aria-label="Categories"><button data-category="All projects" className="selected" aria-pressed="true" disabled>All projects</button><button data-category="Web development" className="" aria-pressed="false" disabled>Web development</button><button data-category="UX & design" className="" aria-pressed="false" disabled>UX & design</button><button data-category="Data & AI" className="" aria-pressed="false" disabled>Data & AI</button><button data-category="Social impact" className="" aria-pressed="false" disabled>Social impact</button><button data-category="Cybersecurity" className="" aria-pressed="false" disabled>Cybersecurity</button></div><BlankListings page="projects" /><p id="empty" hidden>No matches found. Try another search or filter.</p><div className="load-area"><button id="load-more" disabled>Load more projects ＋</button><p id="count" role="status" aria-live="polite"></p></div></section><aside className="tip"><span>♧</span><div><strong>A challenge, not a blank page.</strong><p>Every brief includes a problem to explore, suggested approaches, and a deliverable. Make it your own.</p></div><a href="career-resources.html">Explore career resources →</a></aside><section className="career-cta"><div><p className="eyebrow">A NEXT STEP THAT FEELS LIKE YOU</p><h2>What will you build next?</h2><p>Find opportunities that fit your interests, experience, and goals. Our quiz connects you with a next step that feels like you.</p></div><div><a className="button pale" href="quiz.html">Find my match →</a><small>5 quick questions · 2 minutes · No wrong answers</small></div></section></main>

  </>);
}
