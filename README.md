# obsigo - Obsidian to hugo bridge

A converter/bridge from **[Obsidian](https://obsidian.md)** to **[Hugo](https://gohugo.io)** for Static Website Generation, 
including **foreverlinks** redirects for **[Netlify](https://www.netlify.com)**.

This is super-niche but if you are going to use Obsidian + Hugo + Netlify, this will save you so much time you'll want to hug me ;)  

This is like a v0.1-alpha version but it already handles all of the following...

## Why do we need this?

1. Because Obsidian is great for editing and managing a collection of Markdown files and Hugo is great for 
   generating a static website from Markdown files, BUT:
   - Hugo works best when all your files are named `index.md` (but in different folders of course) but this makes it 
     über-painful to search and manage your posts/articles in Obsidian. (Non-descriptive filenames... seriously Hugo?)
   - Both tools don't agree on the exact same flavor of Markdown (e-g: embedding YouTube videos)
   - They don't agree on the way links should be made from one file to another (the whole `index.md` thing again)
2. Hugo can do basic redirects BUT:
   - They are NOT proper 301 redirects (they are JS redirects, which are bad for SEO)
   - They are NOT foreverlinks (they only redirect from a single URL to another single URL, not from `*/old_slug` or `*/old_slug/` to `current_canoncial_URL`)
3. Hugo short tags have limitations (To be addressed in a future version of obsigo)

## Usage

Run `..path.to../obsigo.sh` from your hugo directory.

Obsigo will read a content source directory (typically `content_src` but could be any location you are managing 
with Obsidian) and write to a destination directory (typically `content`) that `hugo` will then process to 
generate a static site.

Obsigo will also generate foreverlinks, typically by writing redirects to `static/_redirects` (those redirects are
in the format expected by Netlify)

## Features

Obsigo will do the following actions:

### Frontmatter/Metadata/Filenames
 
- Cleanup/Remove unimportant keys from your FrontMatter YAML (IMPORTANT: these changes will be written back 
  to the source directory!)
- Collect slugs & aliases from frontmatter `aliases:`, `slug:`, the filename`.md` or the folder_name`/index.md`
  - Detect duplicates in the above!
  - Generate foreverlinks from the above and save them to a Netlify-compatible `_redirects` file
  - Also add additional customs redirects from `_redirects_base.txt` (if it exists)
- Converting obsidian `/xyz/pagename.md` to hugo `/xyz/pagename/index.md`
- Converting obsidian `/xyz/leaf-node/leaf-node.md` to hugo `/xyz/leaf-node/index.md`
- Automatically handle renamed files. If `/cat/oldname.md` becomes `/cat/newname.md`, obsigo will detect it because the
  frontmatter `slug:` will still be `oldname`. At that point, obsigo will add `oldname` to the frontmatter `aliases:`
  and will change he frontmatter `slug:` to `newname`. (This will, as any alias, generate a foreverlink from `*/oldname` to `/cat/newname`.

### Content

- Convert Obsidian-style markup to Hugo-style:
  - Internal links:
    - `.../xyz/index.md` -> `.../xyz/`
    - `.../xyz/leaf-node/leaf-node.md` -> `.../xyz/leaf-node/`
  - YouTube links:
    - `![TED Talk](https://www.youtube.com/watch?v=M0yhHKWUa0g)` -> `{{< youtube M0yhHKWUa0g >}}`
    - `![TED Talk](https://youtu.be/M0yhHKWUa0g)` -> `{{< youtube M0yhHKWUa0g >}}`
- List all Markdown links found (for auditing)
- List all HTML links found (for auditing)
  - Suggest Markdown equivalents (to be manually applied; useful for cleaning up legacy content)
