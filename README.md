# mksite.py

Makes a basic as hell blog. No pagination, nothing fancy, just markdown, two required template names ('post.html' and 'index.html') and some posts. Might not work too great, then again I didn't mean for this to be all to great anyway.

See `python mksite --help` for the most basic help screen in the world.

### Sample

config.ini:

```ini
[settings]
templates = templates
output = output
static = static
site_root = /
posts = posts

[site]
site_title = My Site
site_email = jsmith@example.com
site_author = John Smith
```

post (ex: hello-world.md)

```markdown
---
title: Hello World!
slug: hello-world
date: 2016-01-06 12PM
category: stuff
author: John Smith
---

This is my post. Category, slug, author, and date are optional. Category defaults to none, author to the site author, date to the current date at build time, and slug to the title. Though you should probably fill out the date.
```

standalone post (about.md):

```markdown
---
title: About Me
slug: title
standalone: true
template: post.html
---

This is my standalone page. Standalone and template are required. The variable `is_standalone` is accessible in the template to check if the page is indeed a standalone page.
```
