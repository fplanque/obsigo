#!/bin/zsh
# This script uses zsh syntax

# Configuration
SRGB_PROFILE="/System/Library/ColorSync/Profiles/sRGB Profile.icc"
XATTR_NAME="user.srgb_converted"

# Function to check if image is already sRGB
check_colorspace() {
    profile=$(magick identify -format "%[profile:icc]\n" "$1")
    [[ "$profile" == *"sRGB"* ]]
    return $?
}

# Function to mark file as processed
mark_processed() {
    xattr -w "$XATTR_NAME" "1" "$1" >/dev/null
}

# Find files and process xattr test separately
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.heic" \) -print0 | while IFS= read -r -d '' img; do
    # Skip if already processed, redirecting all output to /dev/null
    xattr -p "$XATTR_NAME" "$img" >/dev/null 2>&1 && continue

    temp="${img}.tmp"

    if [[ ${(L)img} = *.heic ]]; then
        jpeg_name="${img:r}.jpeg"
        echo "Converting HEIC to JPEG with sRGB: $img -> .jpeg"

        magick "$img" -profile "$SRGB_PROFILE" "$jpeg_name" && {
            rm "$img"
            mark_processed "$jpeg_name"
        } || {
            echo "!! ERROR converting HEIC: $img"
        }
    elif ! check_colorspace "$img"; then
        echo "Converting to sRGB: $img"
        magick "$img" -profile "$SRGB_PROFILE" "$temp" && {
            mv "$temp" "$img"
            mark_processed "$img"
        } || {
            rm -f "$temp"
            echo "!! ERROR converting to sRGB: $img"
        }
    else
        echo "Skipping (already sRGB): $img"
        mark_processed "$img"
    fi
done
