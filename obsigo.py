#! python3
# Preprocess markdown files in a directory before passing to Hugo

import os
import shutil

# pip install python-frontmatter
import frontmatter
from io import BytesIO
import re

import yaml

print("Obsigo v0.5 - Preprocess Obsidian markdown files for Hugo")

# Process the frontmatter of the markdown file.
# TODO: converts tags with spaces to tags with hyphens
def process_frontmatter(src_metadata, rel_src_filepath, rel_dest_filepath, site_aliases_dict, stats_dict ):
    source_changed = False      # Source data has not changed yet

    # Cleanup/Remove unimportant keys:
    for key in unimportant_frontmatter_keys:
        if key in src_metadata:
            print(f"  Cleanup: Removing key from source '{key}: {src_metadata[key]}")
            del src_metadata[key]
            source_changed = True
            stats_dict['frontmatter_source_cleanups'] += 1


    # Remove 'visibility' key if its value is 'published'
    if 'visibility' in src_metadata and src_metadata['visibility'] == 'published':
        print(f"  Cleanup: Removing key 'visibility': {src_metadata['visibility']}")
        del src_metadata['visibility']
        source_changed = True
        stats_dict['frontmatter_source_cleanups'] += 1

    if 'draft' in src_metadata:
        draft = src_metadata['draft']
    else:
        draft = False

    # ---

    # Collect aliases:
    if 'aliases' in src_metadata:
        # Make a copy of the aliases
        post_collected_aliases = src_metadata['aliases'].copy()
        # make sure it is a list
        if not isinstance(post_collected_aliases, list):
            post_collected_aliases = [post_collected_aliases]
        stats_dict['aliases_collected'] += len(post_collected_aliases)
    else:
        post_collected_aliases = []
    # print(f"  Collected Aliases: {post_collected_aliases}")

    # Also add the last directory of the file path (not the filename) as an alias
    split_path = rel_src_filepath.split('/')
    print( f"  Split path: {split_path} {len(split_path)}")
    if split_path[-1] == 'index.md' or split_path[-1] == '_index.md':
        # We are in a sub directory if we have a parent:
        if len(split_path) >= 2:
            # we have a parent: add the last directory of the file path (not the filename) as an alias
            main_slug = split_path[-2]
            post_collected_aliases.append(main_slug)
            stats_dict['slugs_collected'] += 1
            print(f"  CONTENT SUBDIR - Adding last directory '{main_slug}' as an alias.")
        else:
            # no parent
            main_slug = None
    else:
        # We have a file name, not an `index.md` file
        # Use the last part of the file path as the main slug
        # remove .md from the end of the folder_name
        # Can be an article, can also be search.md
        main_slug = re.sub(r'\.md$', '', split_path[-1])
        post_collected_aliases.append(main_slug)
        stats_dict['slugs_collected'] += 1
        print(f"  NAMED MD - Adding last directory '{main_slug}' as an alias.")

    print(f"  Main slug: {main_slug}" )
    print(f"  Collected Aliases: {post_collected_aliases}")

    # --

    # Fix 'slug:' in source if necessary:
    if main_slug is None:
        # root _index.md, do nothing
        print( "    Home page, no slug needed.")
        pass

    elif 'slug' not in src_metadata:
        # No 'slug', let's add it:
        print(f"    Adding missing slug to source: '{main_slug}'")
        src_metadata['slug'] = main_slug
        source_changed = True
        stats_dict['missing_slugs_fixed'] += 1

    elif str(src_metadata['slug']) != main_slug:
        # Also add the slug as an alias if it's different from the main slug extracted from the file path
        # DIVERGENT slug found!
        # We need to roll the slugs:
        print(f"    Divergent slugs found: '{src_metadata['slug']}' != '{main_slug}'")
        # Old slug must become an alias:
        post_collected_aliases.append(src_metadata['slug'])
        stats_dict['divergent_slugs_fixed'] += 1    # Old slug becomes an alias and filename becomes new slug
        # add to the original aliasses if not already there:
        if not 'aliases' in src_metadata:
            src_metadata['aliases'] = []
        if src_metadata['slug'] not in src_metadata['aliases']:
            src_metadata['aliases'].append(src_metadata['slug'])
        # the new slug must become the canoncial slug:
        src_metadata['slug'] = main_slug
        source_changed = True

    # ---

    # Build page URI:

    # remove /_?index.md$ from the end of the canonical_uri:
    # print( f"    Relative file path: {rel_dest_filepath}")
    canonical_uri = re.sub(r'/_?index\.md$', '/', '/'+rel_dest_filepath)
    # print( f"    canonical_uri: {canonical_uri}")
    # If there is still a trailing .md, remove it (can happen for search.md for example)
    canonical_uri = re.sub(r'\.md$', '/', canonical_uri)
    # print( f"    canonical_uri: {canonical_uri}")

    # Build redirects: (site aliases)

    for alias in post_collected_aliases:
        # Make sure alias is a string
        alias = str(alias)
        # Keep only the last part of the alias --> NO, we actually want to handle aliases like STMag/index.html
        # alias = alias.split('/')[-1]

        if alias in site_aliases_dict:
            print(f"!!!WARNING!!! Alias '{alias}' already exists in the dictionary.")
            stats_dict['foreverlinks_conflicts_detected'] += 1
        else:
            if draft:
                print(f"  NOT ADDING alias {alias}->{canonical_uri} because it's a draft.")
            else:
                site_aliases_dict[alias] = canonical_uri
                print(f"  Added alias {alias}->{canonical_uri} to the dictionary.")
                stats_dict['foreverlinks_collected'] += 1

    return source_changed



# Extract and print all links from the markdown content:
def process_links(content, file_path):
    # Initialize the Hugo content with the original content
    hugo_content = content

    markdown_links = re.findall(r'(!?\[(.*?)\]\((.*?)\))', content)
    if markdown_links:
        print(f"  MD Links found in {file_path}:")
        for match in markdown_links:
            full_md_link, link_text, link_url = match
            print(f"    - {full_md_link}")

            # Check if the link is a YouTube embed and convert to Hugo tag
            if full_md_link.startswith('!') and ('youtube.com/watch' in link_url or 'youtu.be/' in link_url):
                youtube_id = re.findall(r'(?:https?://(?:www\.)?youtube\.com/watch\?v=|https?://youtu\.be/)([\w-]+)', link_url)
                if youtube_id:
                    hugo_tag = f'{{{{< youtube {youtube_id[0]} >}}}}'
                    print(f"      - Converting YouTube link to Hugo tag: {hugo_tag}")
                    hugo_content = hugo_content.replace(full_md_link, hugo_tag)
                    stats_dict['youtube_links_converted'] += 1

            # Check if the link ends in index.md and remove it
            elif link_url.endswith('/index.md'):
                print(f"      - Removing 'index.md' from the link")
                hugo_content = hugo_content.replace(full_md_link, f"[{match[1]}]({link_url.replace('/index.md', '/')})")
                stats_dict['links_removed_index.md'] += 1

            else:
                # TODO: check if the link repeats the filename like /xyz/filename/filename.md
                # print( f"      - Checking for repeated filename in link: {link_url}")
                parts = link_url.split('/')
                if len(parts) >= 2 and parts[-1] == parts[-2]+".md":
                    print( f"        - Repeated filename found: {parts[-1]}")
                    # remove the last part
                    new_link_url = '/'.join(parts[:-1])+ '/'
                    print( f"        - New link: {new_link_url}")
                    hugo_content = hugo_content.replace(full_md_link, f"[{match[1]}]({new_link_url})")
                    stats_dict['links_removed_duplicate_filename.md'] += 1

    # Find HTML links
    # html_links = re.findall(r'(<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\2>(.*?)<\/a>)', content)
    html_links = re.findall(r'(<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\2.*?>(.*?)<\/a>)', content)
    if html_links:
        print(f"  HTML Links found in {file_path}:")
        for match in html_links:
            print(f"    - {match[0]}")
            markdown_link = f"[{match[3]}]({match[2]})"
            print(f"      - MD equiv: {markdown_link}")
            # replace in the content
            # content = content.replace(full_md_link, markdown_link)

    return content, hugo_content


# Process a single markdown file:
def process_file(file_path, rel_src_filepath, dest_root, site_aliases_dict, stats_dict):

    stats_dict['source_md_files'] += 1

    # Load the file with frontmatter lib:
    post = frontmatter.load(file_path)
    if "title" in post:
        print( f"  Title: {post['title']}")

    # DESTINATION PATH:

    # Check if the filename ends in _?index.md or search.md
    if re.search(r'(/|^)(_?index|search)\.md$', rel_src_filepath):
        rel_dest_filepath = rel_src_filepath
        print(f"  ALREADY INDEX - keep as is: {rel_dest_filepath}")
    else:
        print(f"  NOT INDEX.MD...")
        # Get the filename without the extension
        filename_base = re.sub(r'\.md$', '', os.path.basename(rel_src_filepath))
        # Get the last directory from the path
        lastlevel_dir = os.path.basename(os.path.dirname(rel_src_filepath))
        if filename_base == lastlevel_dir:
            rel_dest_filepath = os.path.join( os.path.dirname(rel_src_filepath), 'index.md')
            print(f"  FILE == DIR - keep only one: {rel_dest_filepath}")
        else:
            # Need to make a leaf directory with index.md
            rel_dest_filepath = re.sub(r'\.md$', '/index.md', rel_src_filepath)
            print(f"  FILE != DIR - Make new leaf directory: {rel_dest_filepath}")

    # Process the frontmatter
    source_changed = process_frontmatter(post.metadata, rel_src_filepath, rel_dest_filepath, site_aliases_dict, stats_dict)

    # Extract and print links from the content and update the content
    new_src_content, new_hugo_content = process_links(post.content, rel_src_filepath )

    # Replace ` # ` with ` \# ` in the destination content only (otherwise Hugo will try to render h1s
    # in case of bullet lists entries like '- # of sectors per track')
    new_hugo_content = re.sub(r' # ', r' \# ', new_hugo_content)

    # Check if the source content has changed
    if new_src_content != post.content:
         post.content = new_src_content
         source_changed = True

    # Check if the filename is a bland index.md
    if re.search(r'/index\.md$', rel_src_filepath):
        print(f"  BLAND index.md - Renaming to to slug: {post.metadata['slug']}.md")
        # Rename the file to the slug
        new_filename = str(post.metadata['slug']) + '.md'
        new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
        print(f"  Renaming file: {file_path} -> {new_file_path}")
        os.rename(file_path, new_file_path)
        stats_dict['index_md_files_renamed'] += 1


    # Save the modified source file only if changes were made
    if not source_changed:
        print("  SOURCE unchanged.")
    else:
        print(f"  Saving modified SOURCE file: {file_path} ...")
        # Create an in-memory bytes buffer
        f = BytesIO()
        # Dump the front matter into the bytes buffer
        frontmatter.dump(post, f)
        with open(file_path, 'wb') as output_file:
            output_file.write(f.getvalue())

    # -----------------------
    # Save the new Hugo content to the destination path
    post.content = new_hugo_content


    dest_file_path = os.path.join(dest_root, rel_dest_filepath)
    # Check if we need to create the directory:
    dest_dir = os.path.dirname(dest_file_path)
    if not os.path.exists(dest_dir):
        print(f"  Creating destination directory: {dest_dir}")
        os.makedirs(dest_dir)

    print(f"  Saving Hugo file: {dest_file_path} ...")
    # Create an in-memory bytes buffer for the Hugo content
    f = BytesIO()
    # Dump the front matter into the bytes buffer
    frontmatter.dump(post, f)
    with open(dest_file_path, 'wb') as output_file:
        output_file.write(f.getvalue())



# Recursively process all markdown files in a directory:
def process_directory(source_directory, destination_directory, site_aliases_dict, stats_dict ):
    for root, dirs, files in os.walk(source_directory):

        cur_dirname = os.path.basename(root)
        if cur_dirname.startswith('.'):
            # print()
            # print()
            # print(f"Skipping hidden directory: {root}")
            continue

        print()
        print()
        # print(f"Processing directory: {root} ... files:{files} ... subdirs: {dirs} ...")
        print(f"Processing directory: {root} ... ")

        if cur_dirname == '_assets':
            # Copy the _assets directory to the destination
            source_assets_path = root
            relative_assets_path = os.path.relpath(source_assets_path, source_directory)
            dest_assets_path = os.path.join(destination_directory, relative_assets_path)

            if not os.path.exists(dest_assets_path):
                print()
                print(f" Copying _assets directory from {source_assets_path} to {dest_assets_path}")
                shutil.copytree(source_assets_path, dest_assets_path)

            continue

        # Else this is a regular directory, process the files
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, source_directory)
                print()
                print(f" Processing file: {relative_file_path} ...")

                process_file(file_path, relative_file_path, destination_directory, site_aliases_dict, stats_dict)


if __name__ == "__main__":

    # Load config
    config_file = "./obsigo.yaml"
    if not os.path.exists(config_file):
        print(f"Configuration file '{config_file}' does not exist.")
        exit(1)
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    source_directory = config['source_directory']
    destination_directory = config['destination_directory']
    src_redirects_base_file = config['src_redirects_base_file']
    dest_redirects_file = config['dest_redirects_file']
    unimportant_frontmatter_keys = config['unimportant_frontmatter_keys']




    site_aliases_dict = {}

    # Check if teh source directory exists
    if not os.path.exists(source_directory):
        print(f"Source directory '{source_directory}' does not exist.")
        exit(1)

    # Ensure the destination directory is empty
    if os.path.exists(destination_directory):
        shutil.rmtree(destination_directory)
    os.makedirs(destination_directory)


    stats_dict = {
        'source_md_files': 0,
        'frontmatter_source_cleanups': 0,
        'youtube_links_converted': 0,
        'aliases_collected': 0,
        'slugs_collected': 0,
        'index_md_files_renamed': 0,  # index.md files renamed to slug.md
        'divergent_slugs_fixed': 0, # Old slug becomes an alias and filename becomes new slug
        'missing_slugs_fixed': 0,   # Missing slug added to source
        'foreverlinks_collected': 0,
        'foreverlinks_conflicts_detected': 0,
        'links_removed_index.md': 0,
        'links_removed_duplicate_filename.md': 0
    }

    process_directory( source_directory, destination_directory, site_aliases_dict, stats_dict )

    # Display the aliases dictionary in alphabetical order:
    site_aliases_dict = dict(sorted(site_aliases_dict.items()))
    print("\nAliases dictionary:")
    # for alias, uri in aliases_dict.items():
        # print(f"  {alias} -> {uri}")
    print(f"  Total aliases: {len(site_aliases_dict)}")
    # Write it to a netlify _redirects file:
    with open( dest_redirects_file, 'w') as f:
        for alias, uri in site_aliases_dict.items():
            f.write(f"*/{alias} {uri} 301\n")

        # Add the contents of ./static/_redirects_base.txt to this file:
        if os.path.exists(src_redirects_base_file):
            print(f"  Adding contents of {src_redirects_base_file} to {dest_redirects_file}")
            with open(src_redirects_base_file, 'r') as base_file:
                f.write(base_file.read())


    print("\nDone.")

    # Display stats:
    print("\nStats:")
    for key, value in stats_dict.items():
        print(f"  {key}: {value}")
