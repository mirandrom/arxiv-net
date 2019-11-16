import json

import dash
import dash_auth
import redis

from arxiv_net.dashboard import DASH_DIR

db = redis.StrictRedis(port=6379)

external_stylesheets = [
    "https://unpkg.com/tachyons@4.10.0/css/tachyons.min.css",
    "https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css"
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True

# Set up simple user accounts
with open(f'{DASH_DIR}/auth.json', 'r') as f:
    VALID_USERNAME_PASSWORD_PAIRS = json.load(f)
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
