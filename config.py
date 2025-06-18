import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Canvas settings
    DEFAULT_CANVAS_WIDTH = 800
    DEFAULT_CANVAS_HEIGHT = 600
    MAX_CANVAS_WIDTH = 1200
    MAX_CANVAS_HEIGHT = 900
    
    # Drawing settings
    MAX_SHAPES_PER_DRAWING = 25
    MIN_SHAPES_PER_DRAWING = 5
    
    # API settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}