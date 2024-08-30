# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re

from setuptools import setup

current_directory = os.path.dirname(__file__)
readme_filename = 'README.md'
readme_path = os.path.join(current_directory, readme_filename)

readme = ""
try:
    with open(readme_path, 'r') as f:
        readme = f.read()
except IOError as e:
    print(e)
    print("Failed to open %s" % readme_path)

with open('serializable/__init__.py', 'r') as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        f.read(),
        re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

if __name__ == '__main__':
    setup(
        name='serializable',
        version=version,
        description="Base class with serialization helpers for user-defined Python objects",
        author="Alex Rubinsteyn",
        author_email="alex@openvax.org",
        url="https://github.com/iskandr/serializable",
        license="http://www.apache.org/licenses/LICENSE-2.0.html",
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Operating System :: OS Independent',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python',
        ],
        install_requires=[
            "typechecks>=0.0.2",
        ],
        long_description=readme,
        long_description_content_type='text/markdown',
        packages=['serializable'],
    )
