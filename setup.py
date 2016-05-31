from distutils.core import setup

VERSION = '0.1'

setup(
    name = 'pyattr',
    packages = ['pyattr'],
    test_requires = ['nose'],
    version = VERSION,
    description = 'Yet another class attribute helper.',
    author = 'Flávio Lisbôa',
    author_email = 'flisboa.costa@gmail.com',
    url = 'https://github.com/flisboac/pyattr',
    download_url = 'https://github.com/flisboac/pyattr/tarball/%s' % VERSION,
    keywords = ['attribute', 'property', 'helper', 'meta'],
    classifiers = [],
)