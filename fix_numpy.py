#!/usr/bin/env python3
"""Fix numpy recipe to handle v-prefix git tags."""
import os

paths = [
    os.path.expanduser('~/.buildozer/android/platform/python-for-android/pythonforandroid/recipes/numpy/__init__.py'),
]

for p in paths:
    if not os.path.exists(p):
        print(f'Not found: {p}')
        continue
    with open(p) as f:
        c = f.read()
    if "if not self.version.startswith('v')" in c:
        print(f'Already fixed: {p}')
        continue
    init = '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.version.startswith('v'):
            self.version = 'v' + self.version
'''
    c = c.replace('min_ndk_api_support = 24', 'min_ndk_api_support = 24' + init)
    with open(p, 'w') as f:
        f.write(c)
    print(f'Fixed: {p}')
