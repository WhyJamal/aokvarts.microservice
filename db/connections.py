from sqlalchemy import create_engine
from core.config import DATABASES

engines = {
    name: create_engine(url)
    for name, url in DATABASES.items()
}

def get_engine(name: str):
    return engines[name]