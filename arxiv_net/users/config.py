import configparser
from sqlalchemy import create_engine
from arxiv_net.users import USER_DIR

config = configparser.ConfigParser()
config.read(f'{USER_DIR}/config.txt')

engine = create_engine(config.get('database', 'con'))