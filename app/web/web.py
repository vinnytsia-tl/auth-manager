from app.common.web import Web as CommonWeb

from .utils import init_hooks

init_hooks()


# hooks must be initialized before importing controllers
# pylint: disable=wrong-import-position,wrong-import-order

from .controllers import Root  # noqa: E402

# pylint: enable=wrong-import-position,wrong-import-order


class Web:
    @staticmethod
    def start():
        CommonWeb.start(Root())

    @staticmethod
    def stop():
        CommonWeb.stop()
