[app]

# (str) Title of your application
title = 食物营养计算

# (str) Package name
package.name = foodcalc

# (str) Package domain (needed for android/ios packaging)
package.domain = org.foodcalc

# (str) Source code where the main.py live
source.dir = app

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,images/*,data/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests,bin,venv,.git

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = hostpython3==3.9.13,python3==3.9.13,kivy==2.1.0,kivymd==1.2.0,matplotlib==3.5.3,pyperclip==1.8.2,plyer==2.1.0,pillow==9.2.0,numpy==1.22.4

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
# services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OSX Specific
#

#
# author = © Copyright Info

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 1.9.1

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
android.presplash_color = #4CAF50

# (string) Presplash animation using Lottie
# android.presplash_lottie = "path/to/lottie.json"

# (str) Adaptive icon of the application
# android.adaptive_icon_foreground.filename = %(source.dir)s/data/ic_foreground.png
# android.adaptive_icon_background.filename = %(source.dir)s/data/ic_background.png

# (list) Permissions
android.permissions = INTERNET

# (list) features (adds uses-feature -tags to manifest)
# android.features = android.hardware.usb.host

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 24

# (int) Android SDK version to use
# android.sdk = 20

# (str) Android NDK version to use
# android.ndk = 23b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 24

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
# android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
# android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded.)
# android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save time
# when an update is due and you just want to test/build your package
# android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only. If set to False,
# the default, you will be shown the license when first running
# buildozer.
# android.accept_sdk_license = False

# (str) Android entry point, default is ok for Kivy-based app
# android.entrypoint = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Android Activity
# use that parameter together with android.entrypoint to set custom Java class instead of PythonActivity
# android.activity_class_name = org.kivy.android.PythonActivity

# (str) Extra xml attributes to set on the <activity> tag in the AndroidManifest.xml
# android.extra_activity_attributes = android:taskAffinity=""

# (list) Android Java libraries to add (will be added at the libs/ folder and added to the classpath)
# android.add_jars = {}

# (list) Java files to add to the android project (will be added at src/main/java)
# android.add_src =

# (list) Android AAR archives to add
# android.add_aars =

# (list) Add these to the Java classpath for the APK (just find the jar)
# android.add_classpath = {}

# (list) Android gradle dependencies to add
# android.gradle_dependencies =
# android.gradle_repositories =

# (bool) Enable AndroidX support (default is false)
# android.enable_androidx = True

# (list) Gradle packages to exclude from the build
# android.gradle_exclude_packages =

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (int) overrides the version code (default: automatic)
# android.numeric_version = 1

# (int) Minimum Android API level to use for the app (default: automatic based on requirements)
# android.minapi = 21

# (int) Android SDK to use for compilation (default: automatic based on requirements)
# android.api = 31

# (bool) Do not compile non-versioned requirements for Android (no .so files)
# android.ignore_noversion = False

# (list) Java compiler parameters (will be added to the javac command line)
# android.add_java_compiler_parameters =

# (str) Path to a custom whitelist file for permissions
# android.whitelist =

# (str) Path to a custom blacklist file for permissions
# android.blacklist =

# (list) Java classes to add as activities to the manifest.
# android.add_activities =

# (list) Java classes to add as services to the manifest.
# android.add_services =

# (list) Java classes to add as receivers to the manifest.
# android.add_receivers =

# (list) Java classes to add as providers to the manifest.
# android.add_providers =

# (list) Java classes to add as uses-libraries to the manifest.
# android.add_uses_libraries =

# (list) Java classes to add as static broadcast receivers.
# android.add_static_receivers =

# (bool) Specify whether the app is designed for Android TV (default: False)
# android.is_tv = False

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
# ios.kivy_ios_dir = ../kivy-ios
# Alternately, specify the URL and branch of a git checkout:
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# Another platform dependency: ios-deploy
# Uncomment to use a custom checkout
# ios.ios_deploy_dir = ../ios_deploy
# Or specify URL and branch
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0

# (bool) Whether or not to sign the code
ios.codesign.allowed = false

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, default is under app dir
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab) storage
# bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as a option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#
#        [app]
#        source.exclude_patterns = license,data/audio/*.wav,data/images/original/*
#
#    This can be translated into:
#
#        [app:source.exclude_patterns]
#        license
#        data/audio/*.wav
#        data/images/original/*
#


#    -----------------------------------------------------------------------------
#    Profiles
#
#    You can extend section / key with a profile
#    For example, you want to deploy a demo version of your application without
#    HD content. You could first change the title to add "(demo)" in the name
#    and extend the excluded directories to remove the HD content.
#
#        [app@demo]
#        title = My Application (demo)
#
#        [app:source.exclude_patterns@demo]
#        images/hd/*
#
#    Then, invoke the command line with the "demo" profile:
#
#        buildozer --profile demo android debug
