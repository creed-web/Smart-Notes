#!/usr/bin/env python3
"""
Smart Notes Backend Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-notes-secret-key-change-in-production'
    
    # Hugging Face API Configuration
    HUGGINGFACE_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN')
    HUGGINGFACE_MODEL = os.environ.get('HUGGINGFACE_MODEL') or 'google/flan-t5-small'
    
    # Text Processing Configuration
    MAX_CHUNK_SIZE = int(os.environ.get('MAX_CHUNK_SIZE', '1000'))
    MIN_SUMMARY_LENGTH = int(os.environ.get('MIN_SUMMARY_LENGTH', '50'))
    MAX_SUMMARY_LENGTH = int(os.environ.get('MAX_SUMMARY_LENGTH', '300'))
    
    # API Configuration
    REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '1000000'))  # 1MB
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'smart_notes.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
