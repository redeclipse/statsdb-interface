# Set to True to enable debug functions such as Flask's debugging server.
DEBUG = False

# Enables/disables caching
CACHE = not DEBUG

# Enables/disables SQLAlchemy terminal output
SQLALCHEMY_ECHO = DEBUG

# Supress SQLAlchemy deprecation warning
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Bind the web server to this host.
HOST = '0.0.0.0'
# Bind the web server to this port.
PORT = 28700

# Number of results to return in a api list page (e.g. /api/games?page=3).
API_RESULTS_PER_PAGE = 25

# Number of results to return in a highscore list. (e.g. topraces)
API_HIGHSCORE_RESULTS = 10
DISPLAY_HIGHSCORE_RESULTS = 5

# Number of results to return in a display list page.
DISPLAY_RESULTS_PER_PAGE = 15

# Number of results to return in a 'recent' list.
DISPLAY_RESULTS_RECENT = 10
