import os

import settings


def local_path(path):
    return os.path.join(settings.LOCALDIR, path)
