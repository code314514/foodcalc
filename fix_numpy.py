#!/usr/bin/env python3
"""Fix numpy recipe to handle v-prefix git tags."""
import os, glob

# Search in both ~/.buildozer and the project's .buildozer
search_roots = [
    os.path.expanduser('~'),
    os.getcwd(),
]

found = []
for root in search_roots:
    pattern = os.path.join(root, '.buildozer/android/platform/*/pythonforandroid/recipes/numpy/__init__.py')
    found.extend(glob.glob(pattern, recursive=False))
    # Also check project-level .buildozer
    pattern2 = os.path.join(root, '.buildozer/android/platform/python-for-android/pythonforandroid/recipes/numpy/__init__.py')
    if os.path.exists(pattern2):
        found.append(pattern2)

if not found:
    # Last resort: find it
    for root, dirs, files in os.walk(os.getcwd()):
        if '__init__.py' in files and root.endswith('/recipes/numpy'):
            found.append(os.path.join(root, '__init__.py'))
            break
        if root.count(os.sep) > 10:  # don't go too deep
            dirs.clear()

for p in found:
    print(f'Found: {p}')
    with open(p) as f:
        c = f.read()
    if "if not self.version.startswith('v')" in c:
        print('  Already fixed')
        continue
    init_block = '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.version.startswith('v'):
            self.version = 'v' + self.version
'''
    c = c.replace('min_ndk_api_support = 24', 'min_ndk_api_support = 24' + init_block)
    with open(p, 'w') as f:
        f.write(c)
    print('  FIXED')

if not found:
    print('ERROR: numpy recipe not found!')
