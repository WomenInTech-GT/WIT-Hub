import React from 'react';
import mainaboutPhoto from '../images/mainabout.jpg';

export default function Page() {
  return (<>
<main className="container about-main">
        
        <section className="about-hero" aria-labelledby="about-title">
            <div className="about-copy">
                
                <h1 id="about-title">Meet the Team</h1>
                <p className="about-lead">We're here to make your next step in tech feel a lot more possible.</p>
                <p>The Hub brings together career resources, internships, events, and projects selected by Rooted's Women in Tech. One
                    welcoming place to find guidance, build confidence, and discover what comes next.</p><a
                    className="meet-link" href="#team">Meet the people behind it ↓</a>
            </div>
            <div className="team-image-space"><img src={mainaboutPhoto} alt="The Women in Tech community" /></div>
        </section>
        <section className="team-section" id="team" aria-labelledby="team-title">
            <div className="team-heading">
                <div>
                    <p className="eyebrow">THE PEOPLE BEHIND THE POSSIBILITIES</p>
                    <h2 id="team-title">Meet the team</h2>
                    <p>A shared purpose: helping more women find their place in tech.</p>
                </div>
                <aside>
                    <p className="eyebrow">YOUR TEAM HERE</p>
                    <p>People who turn small ideas into clear next steps, useful resources, and real connections.</p>
                </aside>
            </div>
            <div className="team-grid">
                <article className="team-card">
                    <h3>Haoran Duan</h3>
                    <p className="team-role">Backend Developer</p>
                    <p>[Add a short bio: their contribution to The Hub, interests, and what they're excited to share.]
                    </p>
                </article>
                <article className="team-card">
                    <h3>Grace Wang</h3>
                    <p className="team-role">Search & Recommendations</p>
                    <p>[Add a short bio: their contribution to The Hub, interests, and what they're excited to share.]
                    </p>
                </article>
                <article className="team-card">
                    <h3>Livia Kouts</h3>
                    <p className="team-role">Frontend Developer</p>
                    <p>[Add a short bio: their contribution to The Hub, interests, and what they're excited to share.]
                    </p>
                </article>
                <article className="team-card">
                    <h3>Qiao Yi Tan</h3>
                    <p className="team-role">Frontend Analytics</p>
                    <p>[Add a short bio: their contribution to The Hub, interests, and what they're excited to share.]
                    </p>
                </article>
                <article className="team-card">
                    <h3>Jiyeong Hong</h3>
                    <p className="team-role">Technical Content & Projects</p>
                    <p>[Add a short bio: their contribution to The Hub, interests, and what they're excited to share.]
                    </p>
                </article>
                <article className="team-card">
                    <h3>Vivian Tan</h3>
                    <p className="team-role">Mentor</p>
                    <p>[Add a short bio: their contribution to The Hub, interests, and what they're excited to share.]
                    </p>
                </article>
            </div>
        </section>
        <section className="about-cta">
            <div>
                <p className="eyebrow">YOUR NEXT CHAPTER STARTS HERE</p>
                <h2>A little support. A world of possibilities.</h2>
                <p>Explore something new, build on what you know, or find a place to begin. We're glad you're here.</p>
            </div>
            <div><a className="button pale" href="career-resources.html">Explore career resources →</a><small>Find your next
                    step with us.</small></div>
        </section>
        <p className="about-connect">Not sure where to begin? <a href="quiz.html">Find your next step →</a></p>
    </main>

  </>);
}
