import dotenv
import os

class Secrets():
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        dotenv_file = os.path.join(base_dir, ".env")
        dotenv.load_dotenv(dotenv_file)

        if os.getenv('PRODUCTION') == 'True':
            self.SQLALCHEMY_DATABASE_URI = str(os.getenv('DATABASE_URL'))
        else:
            self.SQLALCHEMY_DATABASE_URI = 'http://localhost:5432/'

        self.SECRET_KEY = os.getenv("SECRET_KEY")