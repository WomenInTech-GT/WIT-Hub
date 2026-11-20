import React from 'react';
import imagePhoto from '../images/image.jpg';

export default function Page() {
  return (<>
<main className="container">
        <section className="hero">
            <div>
                <p className="eyebrow">— &nbsp; BUILD. CONNECT. GROW.</p>
                <h1>Resources by<br />Women in Tech, for women in tech</h1>
                <p className="intro">Find events, internships, projects, and career resources curated by Women in Tech.
                    Built to help you grow, connect, and move forward.</p>
                <form className="search" action="#opportunities"><span aria-hidden="true">⌕</span><input
                        aria-label="Search opportunities" placeholder="Try “design”, “entry level”, or “remote”" /><button
                        aria-label="Search">→</button></form><a className="help" href="quiz.html">✧ &nbsp; Not sure where to
                    start? &nbsp;Find something for me →</a>
            </div>
            <div className="hero-visual"><img
                    src={imagePhoto}
                    alt="Students spending time together on campus" /><span className="photo-label">☀ &nbsp; A little
                    curiosity goes a long way.</span>
                <div className="note"><span>↗</span>
                    <div>You don’t need it all figured out.<small>Just a good place to begin.</small></div>
                </div>
                <p className="caption">FIND YOUR PEOPLE. BUILD YOUR FUTURE.</p>
            </div>
        </section>
        <section className="opportunities" id="opportunities">
            <p className="eyebrow">GOOD PLACES TO START</p>
            <div className="section-heading">
                <h2>Small steps. Real possibilities.</h2><a href="#cards">Explore all opportunities →</a>
            </div>
            <div className="filters">
                <div className="tabs"><a className="active" href="#cards">All opportunities</a><a
                        href="events.html">Events</a><a href="internships.html">Internships</a><a
                        href="projects.html">Projects</a><a href="career-resources.html">Career Resources</a></div><small>◉
                    &nbsp;Curated by women in tech</small>
            </div>
            <div className="cards" id="cards" aria-label="Opportunity placeholders"><article className="card blank-card" aria-hidden="true"><div className="card-photo blank-image"></div><div className="card-body"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div><div className="blank-footer"></div></div></article><article className="card blank-card" aria-hidden="true"><div className="card-photo blank-image"></div><div className="card-body"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div><div className="blank-footer"></div></div></article><article className="card blank-card" aria-hidden="true"><div className="card-photo blank-image"></div><div className="card-body"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div><div className="blank-footer"></div></div></article><article className="card blank-card" aria-hidden="true"><div className="card-photo blank-image"></div><div className="card-body"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div><div className="blank-footer"></div></div></article></div>
        </section>
        <section className="match" id="match">
            <div>
                <p className="eyebrow">✧ &nbsp; A NEXT STEP THAT FEELS LIKE YOU</p>
                <h2>So many possibilities.<br />Let’s find your kind of opportunity.</h2>
                <p>Tell us what you’re into. We’ll connect the dots with events, roles, projects, and resources picked
                    for your goals.</p>
            </div>
            <div className="match-action">
                <div><span>Your interests</span><span>Your ambitions</span></div><a className="button pale"
                    href="quiz.html">Find my match <b>→</b></a><small>5 quick questions · 2 minutes · No wrong
                    answers</small>
            </div>
        </section>
        <section className="resources" id="resources">
            <div className="section-heading">
                <h2>A little guidance goes a long way.</h2><a href="career-resources.html">All career resources →</a>
            </div>
            <div className="resource-grid" aria-label="Resource placeholders"><article className="resource blank-card" aria-hidden="true"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div></article><article className="resource blank-card" aria-hidden="true"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div></article><article className="resource blank-card" aria-hidden="true"><div className="blank-meta"></div><div className="blank-title"></div><div className="blank-copy"></div><div className="blank-copy short"></div></article></div>
        </section>
    </main>
<footer id="about">
        <div className="container footer-content"><a className="logo" href="#"><span className="logo-icon">↗</span><span>The
                    Hub<small>by Women in Tech</small></span></a>
            <p>Build. Connect. Grow.</p>
            <nav aria-label="Footer navigation"><a href="career-resources.html">Career Resources</a><a
                    href="internships.html">Internships</a><a href="events.html">Events</a><a
                    href="projects.html">Projects</a></nav>
        </div>
    </footer>
  </>);
}
