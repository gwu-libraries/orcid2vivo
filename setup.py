from setuptools import setup

setup(
    name='orcid2vivo',
    version='0.9.0',
    url='https://github.com/gwu-libraries/orcid2vivo',
    author='Justin Littman',
    author_email='justinlittman@gmail.com',
    py_modules=['orcid2vivo', 'orcid2vivo_loader', 'orcid2vivo_service'],
    packages=['orcid2vivo_app', ],
    scripts=['orcid2vivo.py', 'orcid2vivo_loader.py', 'orcid2vivo_service.py'],
    description="For retrieving data from the ORCID API and crosswalking to VIVO-ISF.",
    platforms=['POSIX'],
    test_suite='tests',
    install_requires=['rdflib>=4.2.0',
                      'requests>=2.7.0',
                      'bibtexparser>=0.6.1',
                      'flask>=0.10.1'],
    tests_require=['vcrpy>=1.7.0',
                   'mock>=1.3.0'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 4 - Beta',
        'Framework :: Flask',
    ],
)
