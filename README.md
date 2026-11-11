# Cloud City

A free, static homepage with one floating island per area of life. No server, no paid plan, no login.

## Files

- `index.html`: the whole site (HTML, CSS, and animation in one file).

## Free hosting options

Pick one. All three are free for a static site like this.

### Option A: Netlify Drop (fastest, no account setup beyond sign-up)
1. Go to https://app.netlify.com/drop
2. Drag the `cloud-city` folder onto the page.
3. You get a public URL immediately. Create a free account to keep it.

### Option B: GitHub Pages
1. Create a new public repository on GitHub, for example `cloud-city`.
2. Upload `index.html` (and this README) to the repository.
3. Go to Settings > Pages, choose "Deploy from a branch", select `main` and `/ (root)`, and save.
4. The site appears at `https://<your-username>.github.io/cloud-city/`.

### Option C: Cloudflare Pages
1. Create a free Cloudflare account and open Workers & Pages > Create > Pages.
2. Upload the folder directly (Direct Upload), or connect the GitHub repo.

## Making the islands do things

Each island is an `<a href="#...">` link in `index.html`. To point one at a real page, change its `href`. For example, `href="kitchen.html"` opens a `kitchen.html` file in the same folder. Keep each new page as a plain HTML file so it stays free to host.
