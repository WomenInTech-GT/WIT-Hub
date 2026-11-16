// Database content is not connected yet. Keep the original layouts as blank slots.
const content = { 'career-resources': null, internships: null, events: null, projects: null };
const page = document.body.dataset.page || 'career-resources';
const grid = document.querySelector('#listings, #guide-grid');
const lines = '<div class="blank-title"></div><div class="blank-copy"></div><div class="blank-copy short"></div>';
const templates = {
 'career-resources': `<article class="guide-card blank-card" aria-hidden="true"><div class="guide-top blank-meta"></div>${lines}<div class="blank-footer"></div></article>`,
 internships: `<article class="listing blank-card" aria-hidden="true"><div class="listing-body"><div class="blank-meta"></div>${lines}<div class="metadata blank-metadata"></div><div class="blank-footer"></div></div></article>`,
 events: `<article class="listing blank-card" aria-hidden="true"><div class="event-row"><div class="date-box blank-date"></div><div>${lines}</div><div class="blank-meta"></div><div class="blank-meta"></div></div></article>`,
 projects: `<article class="listing blank-card" aria-hidden="true"><div class="project-image blank-image"></div><div class="listing-body"><div class="blank-meta"></div>${lines}<div class="project-facts blank-facts"></div><div class="blank-footer"></div></div></article>`
};
grid.innerHTML = templates[page].repeat(page === 'career-resources' ? 9 : 6);
grid.setAttribute('aria-label', 'Content will be available when connected.');
document.querySelectorAll('.search-row input, .search-row select, .sort select, .category-tabs button').forEach(control => { control.disabled = true; });
const load = document.querySelector('#load-more');
if (load) { load.hidden = false; load.disabled = true; }
const count = document.querySelector('#count, #result-count');
if (count) count.textContent = '';
