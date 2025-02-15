import importlib.metadata

from .cli import app


__version__ = importlib.metadata.version(__name__)


if __name__ == "__main__":
    app()
