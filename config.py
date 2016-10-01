# -*- coding: utf-8 -*-

# Set these manually.

# Set to True to enable debug functions such as Flask's debugging server.
DEBUG = True

# Bind the web server to this host.
HOST = '0.0.0.0'
# Bind the web server to this port.
PORT = 28700

# Number of results to return in a api list page (e.g. /api/games?page=3).
API_RESULTS_PER_PAGE = 25

# Number of results to return in a highscore list. (e.g. topraces)
API_HIGHSCORE_RESULTS = 10

# Number of results to return in a display list page.
DISPLAY_RESULTS_PER_PAGE = 15

# Number of results to return in a 'recent' list.
DISPLAY_RESULTS_RECENT = 10


# These are set in other parts of the program.

# Directory containing stats.sqlite (probably the master server home).
data_directory = None
