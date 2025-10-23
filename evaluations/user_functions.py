#!/usr/bin/env python3
"""
User functions for AI Agent evaluations
Following Azure AI Agents SDK patterns from samples/utils/user_functions.py
"""

from agent_functions import get_weather, get_news_articles

# Functions set following Azure SDK pattern
user_functions = {
    get_weather,
    get_news_articles
}

# Alternative naming patterns the action might look for
functions = user_functions
agent_functions = user_functions
available_functions = user_functions

__all__ = ['user_functions', 'functions', 'agent_functions', 'available_functions', 'get_weather', 'get_news_articles']