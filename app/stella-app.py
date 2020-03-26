import sys
import logging
from core import create_app
from core.cron import cron

app = create_app('default')


def main():
    # logger = logging.getLogger("stella-app")
    # logger.info("Starting cron job...")
    # cron(app.app_context()).start()

    logger = logging.getLogger("stella-app")
    logger.info("Starting app...")
    app.run(host='0.0.0.0', port=8000, debug=False)


if __name__ == '__main__':
    sys.exit(main())
