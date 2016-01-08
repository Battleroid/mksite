"""
Usage:
    mksite.py [options] <config>

Options:
    -h --help  Show this screen.
    -n --new  Create new config.
"""

import shutil
from ConfigParser import ConfigParser
from datetime import datetime
import dateutil.parser
from docopt import docopt
from hoedown import Markdown, HtmlRenderer, SmartyPants
from jinja2 import Environment, FileSystemLoader
from slugify import slugify
import errno
import frontmatter
import os
import sys

def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

class HtmlRenderer(HtmlRenderer, SmartyPants):
    pass

class Engine(object):

    defaults = dict(
        posts='posts',
        templates='templates',
        output='output',
        static='static',
        site_root='/'
    )

    site = dict(
        site_title='My Site',
        site_author='John Smith',
        site_email='jsmith@example.com'
    )

    def __init__(self):
        self.args = docopt(__doc__)

        # config
        filename = self.args['<config>']
        self.cf = ConfigParser()

        # create config
        if self.args['--new']:
            for name, sect in [('settings', self.defaults), ('site', self.site)]:
                self.cf.add_section(name)
                for k, v in sect.items():
                    self.cf.set(name, k, v)
            self.cf.write(open(filename, 'w'))

            # create directories
            dirs = ('posts', 'templates', 'static')
            for d in dirs:
                if not os.path.exists(d):
                    os.mkdir(d)
            sys.exit(0)
        
        # load config
        self.cf.read(filename)
        for name, dt in [('settings', self.defaults), ('site', self.site)]:
            if self.cf.has_section(name):
                for k, v in self.cf.items(name):
                    dt[k] = v

        # run
        self.generate()

    def check_directories(self):
        directories = (
            self.defaults['posts'],
            self.defaults['templates'],
            self.defaults['static']
        )
        for d in directories:
            if not os.path.isdir(d):
                print '{} is not a directory or does not exist.'.format(d)
                sys.exit(1)

    def check_templates(self):
        required = ('post.html', 'index.html')
        current = self.env.list_templates()
        for t in required:
            if t not in current:
                print 'Missing {} template'.format(t)
                sys.exit(1)

    def load_posts(self):
        queue = []
        for root, dirs, files in os.walk(self.defaults['posts']):
            for f in files:
                if f.endswith('.md'):
                    queue.append(os.path.join(root, f))

        # process
        for p in queue:
            fm = frontmatter.load(p)
            # check if post or standalone
            standalone = bool(fm.get('standalone', False))
            if standalone:
                print '{} is a standalone page'.format(p)
                post = dict(
                    title=fm.get('title', 'Untitled'),
                    slug=slugify(unicode(fm.get('slug') or fm.get('title'))),
                    template=fm.get('template'),
                    content=Markdown(HtmlRenderer()).render(fm.content)
                )
                self.standalones.append((p, post, ))
                continue

            # is post, fill out meta data
            post = dict(
                meta=dict(
                    category=fm.get('category', 'none')
                ),
                title=fm.get('title', 'Untitled'),
                slug=slugify(unicode(fm.get('slug') or fm.get('title'))),
                author=fm.get('author', self.site.get('site_author', 'Anonymous')),
                content=Markdown(HtmlRenderer()).render(fm.content)
            )
            if 'date' in fm.keys():
                post['meta']['date'] = dateutil.parser.parse(fm['date'])
            else:
                post['meta']['date'] = datetime.now()
            post['link'] = os.path.join('posts', post['slug'] + '.html')
            self.posts.append((p, post, ))

    def render_posts(self):
        mkdirp(os.path.join(self.defaults['output'], 'posts'))

        tmpl = self.env.get_template('post.html')
        for filename, post in self.posts:
            html = tmpl.render(site=self.site, post=post)
            with open(os.path.join(self.defaults['output'], 'posts', post['slug'] + '.html'), 'wb') as f:
                f.write(html)

    def render_standalones(self):
        for filename, post in self.standalones:
            tmpl = self.env.get_template(post['template'])
            html = tmpl.render(site=self.site, post=post)
            with open(os.path.join(self.defaults['output'], post['slug'] + '.html'), 'wb') as f:
                f.write(html)

    def prep_output(self):
        try:
            shutil.rmtree(self.defaults['output'])
        except OSError as e:
            pass

    def render_index(self):
        tmpl = self.env.get_template('index.html')
        self.posts.sort(key=lambda x: x[1]['meta']['date'], reverse=True)
        post_dicts = zip(*self.posts)[1]
        with open(os.path.join(self.defaults['output'], 'index.html'), 'wb') as f:
            f.write(tmpl.render(site=self.site, posts=post_dicts))

    def copy_static(self):
        shutil.copytree(self.defaults['static'], os.path.join(self.defaults['output'], self.defaults['static']))

    def generate(self):
        self.posts = []
        self.standalones = []
        self.env = Environment()
        self.env.loader = FileSystemLoader(self.defaults['templates'])

        # do some checks
        self.check_directories()
        self.check_templates()
        self.prep_output()

        # render
        self.load_posts()
        self.render_posts()
        self.render_standalones()
        self.render_index()
        self.copy_static()


if __name__ == '__main__':
    Engine()
