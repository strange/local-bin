#!/usr/bin/env python
import fileinput
import os
import sys

# templates

LOCAL_MEDIA_URL = """
# Serve media files through the local dev server when DEBUG evaluates to
# true.

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     { 'document_root': settings.MEDIA_ROOT }), )
"""

LOAD_LOCAL_SETTINGS = """
# Load local settings should a module named local_settings be on the path.

try:
    from local_settings import *
except ImportError:
    pass
"""

LOCAL_SETTINGS_SKEL = """import os
def project_path(*paths):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *paths)

def repository_path(*paths):
    return project_path(*(('..', ) + tuple(paths)))

MEDIA_ROOT = repository_path('media')
MEDIA_URL = 'http://127.0.0.1:8000/media/'

TEMPLATE_DIRS = (
    project_path('templates'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': repository_path('db', '%(project_name)s.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}"""

GIT_IGNORE = """# Global
*.pyc
*.pyo
.DS_Store

# Project specific
%(project_name)s/local_settings.py

# Repository specific
db/*
media/*
apps/*
"""

REQUIREMENTS_TXT = """
django
fabric
ipython
"""

# helper functions.

def silent_mkdir(dirname):
    """Create a directory. Fail silently if the directory exists."""
    try:
        os.mkdir(dirname)
    except OSError, e:
        if e.errno == 17:
            pass
        else:
            raise

def silent_symlink(src, dst):
    """Create a symlink. Fail silently on any error."""
    try:
        os.symlink(src, dst)
    except OSError:
        pass
    
def touch(filename):
    if not os.path.exists(filename):
        open(filename, 'w').close()

def append_if_not_added(filename, needle):
    """Append needle to f if not already added."""
    try:
        f = open(filename, 'r')
        haystack = f.read()
        f.close()
    except IOError, e:
        if e.errno == 2:
            haystack = None
        else:
            raise
    
    if haystack is None or not needle in haystack:
        f = open(filename, 'a')
        f.write(needle)
        f.close()

def add_if_file_does_not_exist(filename, content):
    if not os.path.isfile(filename):
        f = open(filename, 'a')
        f.write(content)
        f.close()

def replace_in_file(filename, subject, replacement):
    if not replacement.endswith('\n'):
        replacement = '%s\n' % replacement
    for line in fileinput.input(filename, inplace=1):
        if line == subject or line == '%s\n' % subject:
                line = replacement
        sys.stdout.write(line)

def get_project_name():
    project_name = os.path.basename(os.getcwd())
    
    # test if a directory in -- and with the same name as -- current working
    # directory exists.
    if not os.path.isdir(os.path.join(os.getcwd(), project_name)):
        print (u"A directory named '%s' must exist here in order to use "
               u"these utilities." % project_name)
        sys.exit(1)
    
    return project_name

def add_local_settings_skel(project_name):
    """Add a local_settings-file to override default settings."""
    append_if_not_added('%s/settings.py' % project_name, LOAD_LOCAL_SETTINGS)

    local_settings = LOCAL_SETTINGS_SKEL % {
        'project_name': project_name,
    }
    append_if_not_added('%s/local_settings.py.skel' % project_name,
                        local_settings)

def add_local_media_url(path_to_urls):
    """Add a line to urls.py that loads media through the local dev server in
    debug mode.

    """
    append_if_not_added(path_to_urls, LOCAL_MEDIA_URL)

def add_gitignore(project_name):
    """Add defaults from template to .gitignore."""
    append_if_not_added('.gitignore', GIT_IGNORE % {
        'project_name': project_name
    })

# do stuff

if __name__ == "__main__":
    project_name = get_project_name()
    
    silent_mkdir('originals')
    silent_mkdir('db')
    silent_mkdir('media')
    silent_mkdir('static')
    silent_mkdir('static/style')
    silent_mkdir('static/script')
    silent_mkdir('static/images')
    silent_mkdir('static/images/backgrounds')
    silent_mkdir('static/images/icons')
    silent_mkdir('static/images/misc')
    silent_mkdir('%s/templates' % project_name)

    silent_symlink('../static', 'media/static')

    touch('static/style/master.css')
    touch('%s/templates/base.html' % project_name)

    add_if_file_does_not_exist('requirements.txt', REQUIREMENTS_TXT)
    add_local_media_url('%s/urls.py' % project_name)
    add_local_settings_skel(project_name)

    replace_in_file('%s/settings.py' % project_name,
                    "ADMIN_MEDIA_PREFIX = '/media/'",
                    "ADMIN_MEDIA_PREFIX = '/media/admin/'")
