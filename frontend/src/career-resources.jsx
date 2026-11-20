import React from 'react';
import BlankListings from './BlankListings.jsx';


export default function Page() {
  return (<>
<main className="container career-main">

<section className="career-intro"><div><h1>Career<br />Resources</h1><p>Practical advice for whatever comes next: your first résumé, a portfolio you’re proud of, or a conversation that opens a door.</p></div><aside className="matches"><strong>✧ &nbsp; Your Matches</strong><h3>Practical guides for your next step</h3><p>Created with women in tech in mind. Free to explore, wherever you are in your journey.</p></aside></section>
<section className="featured blank-feature" aria-label="Featured content placeholder"><div className="blank-image" aria-hidden="true"></div><div aria-hidden="true"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div><div className="blank-meta"></div><div className="blank-button"></div></div></section>
<section className="library" aria-labelledby="library-title"><div className="section-heading"><div><h2 id="library-title">Advice you can put into practice.</h2><p className="library-count">Free resources · Curated by Women in Tech</p></div><label className="sort">Sort by: <select id="sort" aria-label="Sort resources" disabled><option value="recommended">Recommended</option><option value="shortest">Shortest read</option><option value="title">Title A–Z</option></select></label></div>
<div className="search-row"><label className="resource-search"><span aria-hidden="true">⌕</span><input id="resource-search" type="search" placeholder="Search résumés, interviews, portfolios…" aria-label="Search resources" disabled /></label><select id="format" aria-label="Filter by format" disabled><option value="all">All formats</option><option value="Guide">Guides</option><option value="Worksheet">Worksheets</option><option value="Checklist">Checklists</option></select><select id="stage" aria-label="Filter by career stage" disabled><option value="all">Career stage</option><option value="Starting out">Starting out</option><option value="Applying">Applying</option></select></div>
<div className="category-tabs" role="group" aria-label="Resource categories"><button className="selected" aria-pressed="true" data-category="All" disabled>All resources</button><button aria-pressed="false" data-category="Résumés" disabled>Résumés</button><button aria-pressed="false" data-category="Portfolios" disabled>Portfolios</button><button aria-pressed="false" data-category="Interviews" disabled>Interviews</button><button aria-pressed="false" data-category="Networking" disabled>Networking</button><button aria-pressed="false" data-category="Career exploration" disabled>Career exploration</button></div>
<BlankListings page="career-resources" /><p id="empty-state" hidden>No resources found. Try another search or filter.</p><div className="load-area"><button id="load-more" type="button" disabled>Load more resources ＋</button><p id="result-count" role="status" aria-live="polite"></p></div></section>
<section className="career-cta"><div><p className="eyebrow">A NEXT STEP THAT FEELS LIKE YOU</p><h2>You don’t need your whole career mapped out.</h2><p>Tell us about your interests and goals. We’ll match you with resources, projects, events, and internships to help you take the next step.</p></div><div><a className="button pale" href="quiz.html">Find my match →</a><small>5 quick questions · 2 minutes · No wrong answers</small></div></section>
</main>

  </>);
}
