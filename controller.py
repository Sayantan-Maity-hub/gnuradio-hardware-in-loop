"""This script start the flask server in thread and stop by keyboard interrupt"""

import time
import threading
from flask_server import start_flask


def main():

    print("\n Welcome to the cortexlab controller script")

    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print("Flask API available at:")
    print("http://127.0.0.1:5678")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Controller stopped.")


if __name__ == "__main__":
    main()
