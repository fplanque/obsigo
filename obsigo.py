#! python3
# Preprocess markdown files in a directory before passing to Hugo

import os
import shutil

# pip install python-frontmatter
import frontmatter
from io import BytesIO
import re

# Process the frontmatter of the markdown file.
def process_frontmatter(data, relative_file_path, aliases_dict, stats_dict ):
    source_changed = False

    # Cleanup/Remove unimportant keys:
    for key in unimportant_frontmatter_keys:
        if key in data:
            print(f"  Cleanup: Removing key from source '{key}: {data[key]}")
            del data[key]
            source_changed = True
            stats_dict['frontmatter_source_cleanups'] += 1

    # Remove 'visibility' key if its value is 'published'
    if 'visibility' in data and data['visibility'] == 'published':
        print(f"  Cleanup: Removing key 'visibility': {data['visibility']}")
        del data['visibility']
        source_changed = True
        stats_dict['frontmatter_source_cleanups'] += 1

    # Collect aliases
    if 'aliases' in data:
        # Make a copy of the aliases
        aliases = data['aliases'].copy()
        # make sure it is a list
        if not isinstance(aliases, list):
            aliases = [aliases]
        stats_dict['aliases_collected'] += len(aliases)
    else:
        aliases = []


    # Also add the last directory of the file path (not the filename) as an alias
    folder_names = relative_file_path.split('/')
    if len(folder_names) >= 2:
        main_slug = folder_names[-2]
        aliases.append(main_slug)
        stats_dict['slugs_collected'] += 1
    elif len(folder_names) == 1 and 'index.md' not in folder_names[0] :
        # remove .md from the end of the folder_name
        main_slug = re.sub(r'\.md$', '', folder_names[0])
        aliases.append(main_slug)
        stats_dict['slugs_collected'] += 1
    else:
        main_slug = None

    # Also add the slug as an alias if it's different from the main slug extracted from the file path
    if 'slug' in data and data['slug'] != main_slug:
        aliases.append(data['slug'])
        stats_dict['divergent_slugs_collected'] += 1

    # remove _?index.md$ from the end of the canonical_uri:
    canonical_uri = '/' + re.sub(r'_?index\.md$', '', relative_file_path)
    # If there is still a trailing .md, remove it (can happen for search.md for example)
    canonical_uri = re.sub(r'\.md$', '', canonical_uri)

    for alias in aliases:
        # Keep only the last part of the alias
        alias = alias.split('/')[-1]

        if alias in aliases_dict:
            print(f"!!!WARNING!!! Alias '{alias}' already exists in the dictionary.")
        else:
            aliases_dict[alias] = canonical_uri
            print(f"  Added alias {alias}->{canonical_uri} to the dictionary.")
            stats_dict['foreverlinks_collected'] += 1

    return source_changed


# Extract and print all links from the markdown content:
def extract_links(content, file_path):
    # Initialize the Hugo content with the original content
    hugo_content = content

    markdown_links = re.findall(r'(!?\[.*?\]\((.*?)\))', content)
    if markdown_links:
        print(f"  MD Links found in {file_path}:")
        for match in markdown_links:
            print(f"    - {match[0]}")
            # Check if the link is a YouTube embed and convert to Hugo tag
            if match[0].startswith('!') and ('youtube.com/watch' in match[1] or 'youtu.be/' in match[1]):
                youtube_id = re.findall(r'(?:https?://(?:www\.)?youtube\.com/watch\?v=|https?://youtu\.be/)([\w-]+)', match[1])
                if youtube_id:
                    hugo_tag = f'{{{{< youtube {youtube_id[0]} >}}}}'
                    print(f"      - Converting YouTube link to Hugo tag: {hugo_tag}")
                    hugo_content = hugo_content.replace(match[0], hugo_tag)
                    stats_dict['youtube_links_converted'] += 1

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
            # content = content.replace(match[0], markdown_link)

    return content, hugo_content

# Process a single markdown file:
def process_file(file_path, relative_file_path, dest_file_path, aliases_dict, stats_dict):

    stats_dict['source_md_files'] += 1

    # Load the file with frontmatter lib:
    post = frontmatter.load(file_path)
    print( f"  Title: {post['title']}")

    # Process the frontmatter
    source_changed = process_frontmatter(post.metadata, relative_file_path, aliases_dict, stats_dict)

    # Extract and print links from the content and update the content
    new_src_content, new_hugo_content = extract_links(post.content, relative_file_path )
    if new_src_content != post.content:
         post.content = new_src_content
         source_changed = True

    # Save the modified file only if changes were made
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

    # Save the new Hugo content to the destination path
    post.content = new_hugo_content
    print(f"  Saving Hugo file: {dest_file_path} ...")
    # Create an in-memory bytes buffer for the Hugo content
    f = BytesIO()
    # Dump the front matter into the bytes buffer
    frontmatter.dump(post, f)
    with open(dest_file_path, 'wb') as output_file:
        output_file.write(f.getvalue())


# Recursively process all markdown files in a directory:
def process_directory(source_directory, destination_directory, aliases_dict, stats_dict ):
    for root, dirs, files in os.walk(source_directory):
        print()
        print()
        print(f"Processing directory: {root} ...")

        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, source_directory)
                print()
                print(f" Processing file: {relative_file_path} ...")

                # Create destination path
                dest_file_path = os.path.join(destination_directory, relative_file_path)
                dest_dir = os.path.dirname(dest_file_path)
                if not os.path.exists(dest_dir):
                    print(f"  Creating destination directory: {dest_dir}")
                    os.makedirs(dest_dir)

                process_file(file_path, relative_file_path, dest_file_path, aliases_dict, stats_dict)

        # Check for _assets subdirectories and copy them
        for dir_name in dirs:
            if dir_name == '_assets':
                source_assets_path = os.path.join(root, dir_name)
                relative_assets_path = os.path.relpath(source_assets_path, source_directory)
                dest_assets_path = os.path.join(destination_directory, relative_assets_path)

                if not os.path.exists(dest_assets_path):
                    print()
                    print(f" Copying _assets directory from {source_assets_path} to {dest_assets_path}")
                    shutil.copytree(source_assets_path, dest_assets_path)


if __name__ == "__main__":
    source_directory = "./content_src"
    destination_directory = "./content"
    src_redirects_base_file = "./_redirects_base.txt"
    dest_redirects_file = "./static/_redirects"
    unimportant_frontmatter_keys = ['dateset', 'priority', 'addvotes', 'countvotes', 'notifications-flags', 'lastedit-user']

    # all of the above should be real from obsigo.yaml instead of hardcoded:



    aliases_dict = {}

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
        'divergent_slugs_collected': 0,
        'foreverlinks_collected': 0,
    }

    process_directory( source_directory, destination_directory, aliases_dict, stats_dict )

    # Display the aliases dictionary in alphabetical order:
    aliases_dict = dict(sorted(aliases_dict.items()))
    print("\nAliases dictionary:")
    # for alias, uri in aliases_dict.items():
        # print(f"  {alias} -> {uri}")
    print(f"  Total aliases: {len(aliases_dict)}")
    # Write it to a netlify _redirects file:
    with open( dest_redirects_file, 'w') as f:
        for alias, uri in aliases_dict.items():
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
