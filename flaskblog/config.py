"""
Module for setting up configuration for the Flask application.
"""

class Config:
    """
    Configuration class for the Flask application.

    Attributes:
        SQLALCHEMY_DATABASE_URI (str): The URI for the application's database.
    """
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'

    def dummy_method_one(self):
        """
        A dummy method
        """

    def dummy_method_two(self):
        """
        Another dummy method
        """
