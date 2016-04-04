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
    'python-Levenshtein',
    'jsonpickle',
    'pdfkit',
    'markdown'
]

extra_requires = {
    'matfiles_extractor': ['h5py', 'Cython']
}

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
      extra_requires=extra_requires,
      entry_points={
          'console_scripts': ['boxplot-validations=accloud.plots.boxplot_validations:main']
      },
      scripts=['bin/Finder', 'bin/ACcloud']
      )


setup(name='finder',
      author='Johannes Meyer',
      author_email='meyerjo@tf.uni-freiburg.de',
      keywords='framework presentation web',
      extra_requires=extra_requires,
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = accloud.finder:main
      """,
)