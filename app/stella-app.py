import logging
from core import create_app


app = create_app('default')

if __name__ == '__main__':
    logger = logging.getLogger("stella-app")
    logger.info("Starting app...")
    app.run(host='0.0.0.0', port=80, debug=False)