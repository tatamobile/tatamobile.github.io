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

DEFAULT_PAGINATION = 10

I18N_TEMPLATES_LANG = 'en'

THEME = "themes/papyrus"
JINJA_ENVIRONMENT = {
  'extensions': ['jinja2.ext.do']
}

SHOW_DATE_MODIFIED = True
SHOW_ARTICLE_AUTHOR = True
SHOW_ARTICLE_CATEGORY = True

FAVICON = "extra/favicon-32x32.png"
TOUCHICON = "extra/apple-touch-icon.png"

# css
FEED_ALL_ATOM = "feeds.atom"
FEED_ALL_RSS = "feeds.rss"


GOOGLE_ANALYTICS = "G-FXZ3M3DJK6"
ADSENSE_ID = "ca-pub-6011041061943855"
ADSENSE_SLOT_ID = "2644505017"

MD_INCLUDE_BASE_PATH = "sourcecode"

GISGUS_REPO_NAME = "tatamobile/tatamobile.github.io"
GISGUS_REPO_ID = "R_kgDOMugGsw"
GISGUS_CATEGORY_NAME = "Announcements"
GISGUS_CATEGORY_ID = "DIC_kwDOMugGs84Cu6-F"

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

SUBTITLE = "TATAMOBILE's BLOG"
SUBTEXT = "I'm a drawer and author in the TATAMOBILE's Blog."
COPYRIGHT = "© 2025 TATAMOBILE. All rights reserved."