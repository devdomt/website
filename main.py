import datetime
import functools
import os
import urllib
import sqlite3

from flask import Flask, render_template, request, session, g, redirect, url_for, \
     abort, flash
from contextlib import closing

from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from peewee import *
from playhouse.flask_utils import FlaskDB,  get_object_or_404, object_list
from playhouse.sqlite_ext import *


#config
APP_DIR = os.path.dirname(os.path.realpath(__file__))
DATABASE = 'sqliteext:///%s' % os.path.join(APP_DIR, 'blog.db')
DEBUG = False
SECRET_KEY = "devkey"
USERNAME = "admin"
PASSWORD = "admin"

#flask init
app = Flask(__name__)
app.config.from_object(__name__)
flask_db = FlaskDB(app)
database = flask_db.database
oembed_providers = bootstrap_basic(OEmbedCache())


class BlogEntity(flask_db.Model):
    title = CharField()
    slug = CharField(unique = True)
    content = TextField()
    published = BooleanField(index=True)
    timestamp = DateTimeField(default = datetime.datetime.now, index = True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = re.sub('[^\w]+', "-", self.title.lower())
        ret = super(BlogEntity, self).save(*args, **kwargs)

        self.update_search_index()
        return ret


    def update_search_index(self):
        try:
            fts_entry = FTSBlogEntity.get(FTSBlogEntity.entry_id)
        except FTSBlogEntity.DoesNotExist:
            fts_entry = FTSBlogEntity(entry_id = self.id)
            force_insert = True
        else:
            force_insert = False

        fts_entry.content = '\n'.join((self.title, self.content))
        fts_entry.save(force_insert= force_insert)

    @classmethod
    def public(cls):
        return BlogEntity.select().where(BlogEntity.published == True)

    @classmethod
    def search(cls):
        words = [word.strip() for word in query.split() if word.strip()]
        if not words:
            return BlogEntity.select().where(BlogEntity.id == 0)
        else:
            search = ' '.join(words)

        return (FTSBlogEntity
                .select(
                FTSBlogEntity,
                BlogEntity,
                FTSBlogEntity.rank().alias('score')
                ).join(BlogEntity, on = (FTSBlogEntity.entry_id == BlogEntity.id).alias('entry'))
                .where((BlogEntity.published == True) & (FTSBlogEntity.match(search)))
                .order_by(SQL('score').desc()))


    @classmethod
    def get_drafts(cls):
        return BlogEntity.select().where(BlogEntity.published == False)




class FTSBlogEntity(FTSModel):
    entry_id = IntegerField()
    content = TextField()

    class Meta:
        database = database


@app.template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):
    querystring = dict((key, value) for key, value in request_args.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urrlib.urlencode(querystring)



def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner


@app.route('/login/', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        if password == app.config['PASSWORD']:
            session['logged_in'] = True
            session.permanent = True  # Use cookie to store session.
            flash('You are now logged in.', 'success')
            return redirect(next_url or url_for('index'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html', next_url=next_url)


@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
    return render_template('logout.html')


@app.route("/")
def render_main_page():
    return render_template("main.html")


@app.route("/article")
def render_article_page():
    search_query = request.args.get('q')
    if search_query:
        query = BlogEntity.search(search_query)
    else:
        query = BlogEntity.public().order_by(BlogEntity.timestamp.desc())
    return object_list("blogSite.html", query, search = search_query)


@app.route("/prototypes")
def render_prototype_page():
    return render_template("prototypes.html")


@app.route("/projects")
def render_project_page():
    return render_template("projects.html")


@app.route("/whereToFind")
def render_where_page():
    return render_template("whereToFind.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.route('/drafts/')
@login_required
def drafts():
    query = BlogEntity.drafts().order_by(BlogEntity.timestamp.desc())
    return object_list("blogSite.html", query)

@app.route('/<slug>/')
def detail(slug):
    if session.get('logged_in'):
        query =  BlogEntity.select()
    else:
        query = BlogEntity.public()
    entry = get_object_or_404(query, BlogEntity.slug == slug)
    return render_template('blogDetail.html', entry = entry)



def main():
    database.create_tables([BlogEntity, FTSBlogEntity], safe = True)
    app.run()


if __name__ == '__main__':
    main();
