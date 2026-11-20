import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { Header, Footer } from './SiteChrome.jsx';

const root = document.getElementById('root');
const page = root.dataset.page;
const pages = import.meta.glob(['./*.jsx', '!./SiteChrome.jsx', '!./BlankListings.jsx']);

async function renderPage() {
  const Page = page === 'quiz' ? null : (await pages[`./${page}.jsx`]()).default;
  createRoot(root).render(<App Page={Page} />);
}

function App({ Page }) {
  useEffect(() => {
    const target = document.getElementById(window.location.hash.slice(1));
    target?.scrollIntoView({ behavior: 'instant' });
  }, []);

  return (
    <>
      <Header page={page} />
      {Page && <Page />}
      {page !== 'index' && page !== 'quiz' && <Footer />}
    </>
  );
}

renderPage();
