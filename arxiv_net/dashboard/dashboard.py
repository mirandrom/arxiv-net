from typing import NamedTuple

from arxiv_net.dashboard.pages.feeds import PaperFeed


class Dashboard:
    """ Encapsulates all methods related to the dash.
    """
    
    def __init__(self, current_user: str = 'default', feed: PaperFeed = None):
        self.current_user = current_user
        self.feed = feed or PaperFeed(collection=[])
        self.focus_feed = PaperFeed(collection=[])


class HideElement(NamedTuple):
    hide = {'display': 'none'}
    show = {'display': 'block'}


Hider = HideElement()
