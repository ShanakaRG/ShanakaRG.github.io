# Personal research website — Shanaka Ramesh Gunasekara

Content lives in data files. A Python script turns them into a website. You
should never have to open an HTML file.

```bash
pip install -r requirements.txt   # once
python build.py --serve           # build, then preview at localhost:8000
```

---

## Folder layout

```
├── build.py                  the build script — run this after editing anything
├── requirements.txt          two dependencies: Jinja2, PyYAML
│
├── content/                  ← EVERYTHING YOU EDIT LIVES HERE
│   ├── site.yaml             name, role, emails, profile links, menu, interests
│   ├── about.md              your bio, as plain text
│   ├── education.yaml        degrees, newest first
│   ├── experience.yaml       jobs and research positions
│   ├── projects.yaml         research projects
│   ├── publications.bib      your papers, in standard BibTeX
│   ├── presentations.yaml    talks and workshops
│   ├── service.yaml          committee roles, volunteering
│   └── awards.yaml           honours, scholarships, training
│
├── static/                   ← FILES YOU UPLOAD
│   ├── img/
│   │   ├── profile.jpg       your portrait  ← add this
│   │   ├── favicon.svg       the little site icon
│   │   └── projects/         one folder per project
│   │       ├── elephant/
│   │       ├── tactile/
│   │       └── tumour/
│   ├── files/
│   │   ├── cv/               cv.pdf         ← add this
│   │   ├── slides/           conference talks (.pptx, .pdf)
│   │   ├── papers/           author-accepted PDFs
│   │   └── posters/          conference posters
│   ├── css/style.css         all colours, fonts, spacing
│   └── js/main.js            menu, scroll reveal, the animated figure
│
├── templates/                page layouts — Jinja2, same syntax as Flask/Django
│   ├── base.html             header, footer, menu (shared by all pages)
│   ├── index.html
│   ├── background.html
│   ├── research.html
│   ├── publications.html
│   └── awards.html
│
└── docs/                     ← GENERATED. Never edit. Wiped on every build.
                                This is the folder GitHub Pages serves.
```

Each subfolder of `static/` has a short `README.txt` reminding you what goes in
it and how to reference it.

---

## How to make each kind of change

Everything below is a data edit. Run `python build.py` afterwards.

### Add a publication

Paste the BibTeX from IEEE Xplore or Google Scholar into
`content/publications.bib`. Optionally add extra fields:

```bibtex
@inproceedings{gunasekara2026something,
  author    = {Gunasekara, Shanaka Ramesh and Someone, Else},
  title     = {A Transformer for Skeleton-Based Action Recognition},
  booktitle = {IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  year      = {2026},
  pages     = {1--10},
  doi       = {10.1109/CVPR.2026.12345},
  tag       = {CVPR},                          % short label in the left column
  pdf       = {files/papers/cvpr2026.pdf},     % a file inside static/
  slides    = {files/slides/cvpr2026.pptx},
  code      = {https://github.com/ShanakaRG/thing},
  video     = {https://youtube.com/watch?v=...}
}
```

**Publication thumbnails.** The publications page shows each paper as a card
with a small image on the left, grouped by year. To give a paper a thumbnail,
drop a figure into `static/img/pubs/` and add one line to its BibTeX entry:

```bibtex
  image = {img/pubs/gunasekara2021systematic.png},
```

If a paper has no `image`, a small venue tag (like `ICIIS`) is shown in its
place, so thumbnails are always optional. Three demo placeholders are wired in
right now and marked `% DEMO` in `publications.bib` — replace them with real
paper figures when you have them.

`@article` goes under Journal articles; anything else goes under Conference
articles. Your name is bolded automatically — that is what `author_surname` in
`site.yaml` controls. The counts on the home page update themselves.

### Add a project

Copy an entry in `content/projects.yaml`. The only required fields are `slug`,
`title` and `when`. Adding it to the file also adds it to the sidebar index, so
there are no two places to keep in sync.

To attach images and slides:

```yaml
- slug: newproject
  title: My new project
  when: "2026"
  objective: What it set out to do.
  approach: |-
    First paragraph.

    Second paragraph, with a [link](https://example.com) and **bold text**.
  collaborators:
    - Dr. Someone — University of Somewhere
  images:
    - file: img/projects/newproject/result.png
      alt: Description for screen readers
      caption: Caption shown under the image
  files:
    - label: Slides (PPTX)
      file: files/slides/newproject.pptx
  links:
    - label: Paper
      href: https://doi.org/...
```

Paths in `file:` are relative to `static/`, so `img/projects/newproject/result.png`
means `static/img/projects/newproject/result.png`.

### Add a job or a degree

Copy an entry in `content/experience.yaml` or `content/education.yaml`. Setting
`current: true` colours the date amber and adds a dot — use it for whatever you
are doing now, and remove it when that changes.

### Add a travel entry

Edit `content/travel.yaml`. Each entry is a card with photos and a short
write-up. Put photos in `static/img/travel/` and reference them by filename.
While the file has no entries, the page shows a friendly "coming soon" message
automatically.

### Add a blog post

Edit `content/blog.yaml`. Posts appear as **tiles** (newest first), not a list.
Each needs a `title`; optionally a `date`, an `excerpt`, a `url` to link to
(an external post, or a file under `static/`), an `image` (in `static/img/blog/`),
and `tags`. Without an image, a coloured tile with the first letter is shown.
While the file is empty, the page shows "coming soon".

### Change your bio, email, or links

`content/about.md` for the bio. `content/site.yaml` for everything else,
including the menu order and the research-interest tags.

### Change colours or fonts

The top of `static/css/style.css`. Every colour in the site is one of the
variables in the `:root` block, and the dark-mode versions are in the
`@media (prefers-color-scheme: dark)` block just below it. Change a variable
once, and it changes everywhere.

### Text formatting available in YAML and .md files

| You write | You get |
|---|---|
| `[text](https://url)` | a link |
| `**text**` | **bold** |
| `*text*` | *italic* |
| blank line | new paragraph |
| lines starting `- ` | a bullet list |

---

## Running the build

```bash
python build.py            # build once into docs/
python build.py --serve    # build, then serve at http://localhost:8000
python build.py --watch    # rebuild automatically as you edit — leave it running
```

`--watch` is the comfortable way to work: keep it running in one terminal, edit
a YAML file, refresh the browser.

If a YAML file has a syntax error the build stops and tells you the file and
line. The most common cause is a colon inside an unquoted value — wrap the whole
value in quotes if it contains `:` or starts with `[`.

---

## Publishing to GitHub Pages

### First time

1. Create a **public** repository named `ShanakaRG.github.io`.
2. Push this whole folder — including `docs/`.

   ```bash
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/ShanakaRG/ShanakaRG.github.io.git
   git push -u origin main
   ```

3. In the repository, go to **Settings → Pages** and set the source to
   **Deploy from a branch**, branch `main`, folder **`/docs`**. Save.
4. A minute later the site is live at **https://ShanakaRG.github.io**

### Afterwards

```bash
python build.py
git add -A
git commit -m "Add CVPR paper"
git push
```

### Or let GitHub do the building

`.github/workflows/build.yml` runs `build.py` on GitHub every time you push a
change to `content/`, `templates/` or `static/`, and commits the result. With it
enabled you can edit `content/publications.bib` directly in GitHub's web editor
from your phone, and the site rebuilds itself a minute later.

It needs one setting: **Settings → Actions → General → Workflow permissions →
Read and write permissions**.

### A custom domain (optional, about $10–15/year)

Buy a domain, then **Settings → Pages → Custom domain**. At your registrar, point
the apex domain at `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and
`185.199.111.153` with four `A` records, or point `www` at
`ShanakaRG.github.io` with a `CNAME` record. Then tick **Enforce HTTPS**.

---

## Two files to add before you publish

1. `static/img/profile.jpg` — your portrait, square, at least 600×600 px. Until
   it exists the page shows a lettered placeholder instead, so nothing breaks.
2. `static/files/cv/cv.pdf` — your CV.

The slides and PDFs that were attached to your old Wix pages are worth
downloading and dropping into `static/files/slides/`; the matching entries are
already written in `content/projects.yaml`, commented out and ready to enable.
