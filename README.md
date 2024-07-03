# obsigo

A bridge from Obsidian to Hugo for Static Website Generation.

Run `../obsigo.sh` from your hugo directory.

Obsigo will read a source directory (typically `content_src` but could be any location you are managing with Obsidian) 
and write to a destination directory (typically `content`) that `hugo` will process to generate a static site.

Obsigo can also generate foreverlinks, typically by writing to `static/_redirects`.

Obsigo will do the follwoing actions:

- Cleanup/Remove unimportant keys from your FrontMatter YAML (IMPORTANT: these changes will be written back to the source directory!)
- Collect slugs & aliases from frontmatter `aliases:`, `slug:`, the filename`.md` or the folder_name`/index.md`
  - Generate foreverlinks from the above and save them to a Netlify-compatible `_redirects` file
- Convert Obsidian-style markup to Hugo-style:
  - `![TED Talk](https://www.youtube.com/watch?v=M0yhHKWUa0g)` -> `{{< youtube M0yhHKWUa0g >}}`
  - `![TED Talk](https://youtu.be/M0yhHKWUa0g)` -> `{{< youtube M0yhHKWUa0g >}}`
- List all markdown links found (for auditing)
- List all HTML links found (for auditing)
  - Suggest Markdown equivalents (to be manually applied; useful for cleaning up legacy content)