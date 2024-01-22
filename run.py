"""
This script initializes the Flask app using the application factory
and runs the app. It also loads the environment variables from the
.env file before initializing the app.
"""

from flaskblog import create_app
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)