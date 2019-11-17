from typing import List, Optional


class PaperFeed:
    """" A tracker for displayed / selected papers
    """
    
    def __init__(self,
                 collection: List[str],
                 selected: Optional[int] = None,
                 display_size: int = 10,
                 ):
        self.collection = collection
        self.display_size = display_size
        self.selected = selected
        self.current_page = 0
        self.total_pages = len(self.collection) // display_size + 1
    
    @property
    def displayed(self):
        return self.collection[self.display_size * self.current_page:
                               self.display_size * self.current_page + self.display_size]
    
    def __call__(self, *args, **kwargs):
        return self.displayed
    
    def reset(self):
        self.collection = list()
        self.selected = None
        self.current_page = 0
    
    def pg_up(self):
        self.current_page += 1
    
    def pg_down(self):
        self.current_page -= 1
