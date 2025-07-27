[app]
android.release_keystore = key.keystore
android.release_keystore_pass = agus99
android.release_keyalias = smash_app
android.release_keyalias_pass = agus99
title = SSBU - Stage Selector [by Zaichu]
package.name = ssbu_stage_selector
package.domain = org.zaichu
version = 1.0.0

source.dir = .
source.include_exts = py,png,jpg,ttf
include_patterns = img/*.png, smash_icon.png
icon.filename = smash_icon.png

orientation = landscape
fullscreen = 1

requirements = python3,kivy,pillow,cython==0.29.34,python-for-android==2024.10.1

[p4a]
patches = patches/fix_long.patch

[android]
android.permissions = INTERNET
android.minapi = 21
android.api = 33
android.gradle_version = 7.0.2

[buildozer]
log_level = 2
warn_on_root = 1
