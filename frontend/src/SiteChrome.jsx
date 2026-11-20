import React from 'react';

export function Header({ page }) {
  return (<header className="site-header"><div className="site-header-inner"><a className="site-brand" href="index.html"><span className="site-brand-icon" aria-hidden="true">↗</span><span>The Hub</span></a><nav className="site-nav" aria-label="Main navigation"><a href="career-resources.html" aria-current={page === 'career-resources' ? 'page' : undefined}>Career Resources</a><a href="internships.html" aria-current={page === 'internships' ? 'page' : undefined}>Internships</a><a href="events.html" aria-current={page === 'events' ? 'page' : undefined}>Events</a><a href="projects.html" aria-current={page === 'projects' ? 'page' : undefined}>Projects</a><a href="about.html" aria-current={page === 'about' ? 'page' : undefined}>About Us</a></nav><div className="site-actions"><a className="site-saved" href="index.html#opportunities"><svg width="16" height="19" viewBox="0 0 16 20" fill="none" aria-hidden="true"><path d="M3 2h10v16l-5-3.5L3 18V2Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/></svg><span>Saved</span></a><a className="site-match" href="quiz.html">Find my match <span aria-hidden="true">✧</span></a></div></div></header>);
}

export function Footer() {
  return (<footer className="career-footer">
        <div className="container">
            <div className="footer-top">
                <div><a className="logo" href="index.html"><span className="logo-icon">↗</span><span>The Hub<small>by Women in
                                Tech</small></span></a>
                    <p>Build. Connect. Grow.</p>
                </div>
                <div>
                    <h3>EXPLORE THE HUB</h3><a href="career-resources.html">Career resources</a><a
                        href="internships.html">Internships</a><a href="events.html">Events</a><a
                        href="projects.html">Projects</a>
                </div>
                <div>
                    <h3>GROW WITH US</h3><a href="about.html">About The Hub</a>
                </div>
                <div className="women-mark">women<sup>✦</sup><br />in tech</div>
            </div>
            <div className="footer-bottom">© 2026 Women in Tech · Resources for your next chapter.</div>
        </div>
    </footer>);
}
