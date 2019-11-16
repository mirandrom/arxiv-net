import os

import dash
from flask_login import LoginManager, UserMixin

from arxiv_net.users.config import config
from arxiv_net.users.users_mgt import db, User as base

external_stylesheets = [
    "https://unpkg.com/tachyons@4.10.0/css/tachyons.min.css",
    "https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css"
]
app = dash.Dash(
    __name__,
    meta_tags=[
        {
            'charset': 'utf-8',
        },
        {
            'name'   : 'viewport',
            'content': 'width=device-width, initial-scale=1, shrink-to-fit=no'
        }
    ],
    external_stylesheets=external_stylesheets

)
server = app.server
app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

# config
server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI=config.get('database', 'con'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

db.init_app(server)

# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'


# Create User class with UserMixin
class User(UserMixin, base):
    pass


# callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
