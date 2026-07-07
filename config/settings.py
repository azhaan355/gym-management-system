# ============================================================
# GYM MANAGEMENT SYSTEM - Configuration
# File: config/settings.py
# ============================================================


class Config:
    """Base configuration — shared across all environments."""

    # Flask
    SECRET_KEY = 'your-secret-key-change-this-in-production'

    # MySQL — Base defaults (overridden by child classes)
    MYSQL_HOST     = 'localhost'
    MYSQL_USER     = 'root'
    MYSQL_PASSWORD = '1NT23CS139'              # <-- Change to your MySQL password
    MYSQL_DB       = 'gym_management'
    MYSQL_PORT     = 3306
    #MYSQL_CURSORCLASS = 'DictCursor' # Returns rows as dicts instead of tuples


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    SECRET_KEY = 'a-very-strong-secret-key-for-production'
    MYSQL_PASSWORD = 'your-production-db-password'