import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

requires = [
    'hoedown',
    'matplotlib',
    'numpy',
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'waitress',
    'python-Levenshtein'
    ]

setup(name='accloud',
      version='0.2',
      description='Tools to conduct and explore ACcloud experiments',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Martin Goth',
      author_email='gothm@tf.uni-freiburg.de',
      url='https://github.com/AC-cloud/tools',
      keywords='web pyramid pylons',
      packages=['accloud'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points={
        'console_scripts': ['boxplot-validations=accloud.plots.boxplot_validations:main']
      },
      scripts=['bin/Finder', 'bin/ACcloud']
)