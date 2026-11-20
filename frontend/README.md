# WIT-Hub frontend

Run these commands from the `frontend` directory:

```sh
npm install
npm run dev
```

Open the local URL printed in the terminal to preview the site. Run `npm run build` to generate the production site in `dist`, and `npm run preview` to serve that build locally.

The React page components live in `src`. The site keeps separate HTML entry points so existing page links still work. Navigation is shared in `src/SiteChrome.jsx`. The resource and opportunity cards are blank placeholders until the backend is connected.
