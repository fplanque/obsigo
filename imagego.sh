#!/bin/zsh
# This script uses zsh syntax

# Configuration
SRGB_PROFILE="/System/Library/ColorSync/Profiles/sRGB Profile.icc"

# Function to check if image is already sRGB
check_colorspace() {
    profile=$(magick identify -format "%[profile:icc]\n" "$1")
    [[ "$profile" == *"sRGB"* ]]
    return $?
}

# Handle all image types in a single loop
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.heic" \) | while read -r img; do
    temp="${img}.tmp"

    if [[ ${(L)img} = *.heic ]]; then
        jpeg_name="${img:r}.jpeg"
        echo "Converting HEIC to JPEG with sRGB: $img -> .jpeg"

        magick "$img" -profile "$SRGB_PROFILE" "$jpeg_name" && {
            rm "$img"
#            echo "Successfully converted HEIC: $jpeg_name"
        } || {
            echo "!! ERROR converting HEIC: $img"
        }
    elif ! check_colorspace "$img"; then
        echo "Converting to sRGB: $img"
        magick "$img" -profile "$SRGB_PROFILE" "$temp" && {
            mv "$temp" "$img"
#            echo "Successfully converted to sRGB: $img"
        } || {
            rm -f "$temp"
            echo "!! ERROR converting to sRGB: $img"
        }
    else
        echo "Skipping (already sRGB): $img"
    fi
done
