import React from 'react';

function BlankLines() {
  return <><div className="blank-title" /><div className="blank-copy" /><div className="blank-copy short" /></>;
}

function BlankCard({ page }) {
  if (page === 'events') {
    return (
      <article className="listing blank-card" aria-hidden="true">
        <div className="event-row">
          <div className="date-box blank-date" />
          <div><BlankLines /></div>
          <div className="blank-meta" />
          <div className="blank-meta" />
        </div>
      </article>
    );
  }

  const isGuide = page === 'career-resources';
  return (
    <article className={isGuide ? 'guide-card blank-card' : 'listing blank-card'} aria-hidden="true">
      {page === 'projects' && <div className="project-image blank-image" />}
      <div className={isGuide ? undefined : 'listing-body'}>
        <div className="blank-meta" />
        <BlankLines />
        {page === 'internships' && <div className="metadata blank-metadata" />}
        {page === 'projects' && <div className="project-facts blank-facts" />}
        <div className="blank-footer" />
      </div>
    </article>
  );
}

export default function BlankListings({ page }) {
  const isGuide = page === 'career-resources';
  return (
    <div className={isGuide ? 'guide-grid' : `listing-grid ${page}`}>
      {Array.from({ length: isGuide ? 9 : 6 }, (_, index) => <BlankCard key={index} page={page} />)}
    </div>
  );
}
