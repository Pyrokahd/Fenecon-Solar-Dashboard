import time

from app import app
application = app.server

if __name__ == '__main__':
    print("waiting 15 secs for volume to load csv...")
    time.sleep(15)
    application.run()