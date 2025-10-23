"""
Agent Functions Module
This module contains all the function implementations for AI Agent evaluations.
"""

from agent_functions import get_weather, get_news_articles

# Export functions for easy discovery
__all__ = ['get_weather', 'get_news_articles']

# Create a functions set for enable_auto_function_calls
user_functions = {get_weather, get_news_articles}