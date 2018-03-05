from setuptools import setup, find_packages
import os

version = '3.2.3.dev0'

setup(name='recensio.translations',
      version=version,
      description="Translations for Recensio",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Programming Language :: Python :: 2.7",
      ],
      keywords='web zope plone translations',
      author='SYSLAB.COM',
      author_email='info@syslab.com',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['recensio'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'infrae.i18nextract',
          'zope.i18nmessageid',
          'zc.testbrowser'
      ],
      extras_require={
          'podiff': ['polib', 'mr.developer'],
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      [console_scripts]
      podiff = recensio.translations:podiff
      updateTranslations = recensio.translations:updateTranslations
      """,
      )
