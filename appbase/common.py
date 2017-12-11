import os

try:
    from converge import settings
except ImportError:
    import settings


def local_path(path):
    return os.path.join(settings.LOCALDIR, path)
