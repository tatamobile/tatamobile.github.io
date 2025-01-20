AUTHOR = 'tower'
SITENAME = 'TATAMOBILE'
SITEURL = ""
ORGNIZATION = "TATAMOBILE"

PATH = "content"

TIMEZONE = 'Asia/Shanghai'

DEFAULT_LANG = 'en'

AUTHORS = {
  'tower': {
    'avatar': '/images/avatars/tower.png',
    'bio': "Graduated in Computer Science and Engineering, but currently working with GNU/Linux infrastructure and in the spare time I'm an Open Source programmer (Python and C), a drawer and author in the TATAMOBILE Blog.",
    'links': [
        ("GitHub", "github", "#"),
        ("Twitter", "twitter", "#"),
        ("Google Plus", "google-plus", "#"),
        ("Facebook", "facebook", "#"),
    ]
  }
}

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None


ARTICLE_URL = 'categories/{category}/{slug}'
ARTICLE_SAVE_AS = 'categories/{category}/{slug}/index.html'

PAGE_URL = '{slug}'
PAGE_SAVE_AS = '{slug}/index.html'

AUTHORS_URL = "authors"
AUTHOR_URL = 'authors/{slug}'
AUTHOR_SAVE_AS = 'authors/{slug}/index.html'

CATEGORIES_URL = "categories"
CATEGORY_URL = 'categories/{slug}'
CATEGORY_SAVE_AS = 'categories/{slug}/index.html'

TAGS_URL = "tags"
TAG_URL = 'tags/{slug}'
TAG_SAVE_AS = 'tags/{slug}/index.html'

# Blogroll
LINKS = (
    ("Pelican", "https://getpelican.com/"),
    ("Python.org", "https://www.python.org/"),
    ("Jinja2", "https://palletsprojects.com/p/jinja/"),
)

# Social widget
SOCIAL = (
    ("E-mail", "envelope", "#"),
    ("GitHub", "github", "#"),
    ("Twitter", "twitter", "#"),
    ("Google Plus", "google-plus", "#"),
    ("Facebook", "facebook", "#"),
    ("Stackoverflow", "stack-overflow", "#"),
    ("GitTip", "gittip", "#"),
    ("Linux User", "linux", "#"),
    ("Feeds", "rss", "feeds.atom"),
)

DEFAULT_PAGINATION = 10

I18N_TEMPLATES_LANG = 'en'

THEME = "themes/pelican-bootstrap3"
JINJA_ENVIRONMENT = {
  'extensions': ['jinja2.ext.i18n', 'jinja2.ext.do']
}

SHOW_DATE_MODIFIED = True
SHOW_ARTICLE_AUTHOR = True
SHOW_ARTICLE_CATEGORY = True

FAVICON = "extra/favicon-32x32.png"
TOUCHICON = "extra/apple-touch-icon.png"

# css
TYPOGRIFY = False
CUSTOM_CSS = "extra/custom.css"
FEED_ALL_ATOM = "feeds.atom"
FEED_ALL_RSS = "feeds.rss"

PYGMENTS_STYLE='monokai'
BOOTSTRAP_THEME='readable'

# navbar
NAVBAR_ELEMENTS = ['menu-items', 'brand-simple']
DISPLAY_PAGES_ON_MENU =False
DISPLAY_CATEGORIES_ON_MENU = False
SUMMARY_MAX_LENGTH = 64
SUMMARY_MAX_PARAGRAPHS = 2
# SITE_LINKS = [
#     ('Home', ''),
#     ('Authors', 'authors'),
#     ('Archives', 'archives'),
#     ('Categories', 'categories'),
#     ('Tags', 'tags'),
#     ('RSS', 'feeds.rss'),
# ]
MENUITEMS = (
            ('Archives', 'archives'),
            ('Categories', 'categories'),
            ('Tags', 'tags'),
            ('Authors', 'authors'),
            ('RSS', 'feeds.rss'),
)

GOOGLE_ANALYTICS = "G-FXZ3M3DJK6"
ADSENSE_ID = "ca-pub-6011041061943855"
ADSENSE_SLOT_ID = "2644505017"

# site banner
SHOW_SITE_BANNER_IN = ['all']
SITE_BANNER_ELEMENTS = ['logo', 'name', 'social']
SITE_BANNER_BACKGROUND_COLOR = "#eeeeec; background-image: url('/images/background_banner.png'); background-repeat: no-repeat; background-size: cover; background-position: center center"
SITELOGO = "images/logo.png"

# sidebar
SIDEBAR_ELEMENTS = ["condensed", "links", "adsense"]
SIDE_BRAND_ELEMENTS = ['logo', 'name', 'social']
CONDENSED_SIDEBAR_ITEMS = ['categories', 'tagcloud', 'recent']

DISPLAY_BREADCRUMBS = True
DISPLAY_CATEGORY_IN_BREADCRUMBS = True

BOOTSTRAP_FLUID = False

TAG_CLOUD_STEPS = 4
TAG_CLOUD_BADGE = True
TAG_CLOUD_MAX_ITEMS=25

MD_INCLUDE_BASE_PATH = "sourcecode"

GITALK_REPO_NAME = "gitalk_comments"
GITALK_REPO_OWNER = "tatamobile"
GITALK_REPO_ADMIN = "tatamobile"

STATIC_PATHS = [
    'images',
    'extra',  # this
]

EXTRA_PATH_METADATA = {
    'extra/favicon.png': {'path': 'favicon.png'},  # and this
    'extra/favicon.ico': {'path': 'favicon.ico'},
    'extra/CNAME': {'path': 'CNAME'},
    'extra/app-ads.txt': {'path': 'app-ads.txt'},
    'extra/ads.txt': {'path': 'ads.txt'},
}