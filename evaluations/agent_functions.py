"""
Helper module for AI agent evaluations
Provides function tool implementations that can be imported by evaluation runners
"""

import json
from datetime import datetime
from typing import Optional


def get_weather(location: str, unit: str = "celsius") -> str:
    """
    Get current weather information for a location.
    This is a mock function that returns simulated weather data.
    
    Args:
        location: City name or location identifier
        unit: Temperature unit ('celsius' or 'fahrenheit')
    
    Returns:
        JSON string with weather information
    """
    # Mock weather data for various cities
    weather_data = {
        "Seattle": {"temp_c": 18, "condition": "Cloudy", "humidity": 75, "wind": 15},
        "Tokyo": {"temp_c": 22, "condition": "Sunny", "humidity": 60, "wind": 10},
        "London": {"temp_c": 12, "condition": "Rainy", "humidity": 85, "wind": 20},
        "New York": {"temp_c": 20, "condition": "Partly Cloudy", "humidity": 70, "wind": 12},
        "Paris": {"temp_c": 15, "condition": "Overcast", "humidity": 80, "wind": 8}
    }
    
    # Find matching city (case-insensitive, partial match)
    location_lower = location.lower()
    matched_city = None
    matched_data = None
    
    for city, data in weather_data.items():
        if city.lower() in location_lower or location_lower in city.lower():
            matched_city = city
            matched_data = data
            break
    
    # Default data if city not found
    if not matched_city:
        matched_city = location
        matched_data = {"temp_c": 20, "condition": "Clear", "humidity": 65, "wind": 10}
    
    # Convert temperature if needed
    temp = matched_data["temp_c"]
    temp_unit = "celsius"
    
    if unit.lower() == "fahrenheit":
        temp = (temp * 9/5) + 32
        temp_unit = "fahrenheit"
    
    # Build response JSON
    response = {
        "location": matched_city,
        "temperature": round(temp, 1),
        "temperature_unit": temp_unit,
        "condition": matched_data["condition"],
        "humidity_percent": matched_data["humidity"],
        "wind_speed_kmh": matched_data["wind"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return json.dumps(response)


def get_news_articles(topic: str, max_articles: int = 5) -> str:
    """
    Get recent news articles for a given topic.
    This is a mock function that returns simulated news data.
    
    Args:
        topic: News topic or category
        max_articles: Maximum number of articles to return
    
    Returns:
        JSON string with news articles
    """
    # Mock news data by category
    news_database = {
        "technology": [
            {"title": "AI Breakthrough in Healthcare", "source": "Tech News", "date": "2025-10-20"},
            {"title": "New Quantum Computing Milestone", "source": "Science Daily", "date": "2025-10-19"},
            {"title": "Cloud Services Expand Globally", "source": "Business Tech", "date": "2025-10-18"},
            {"title": "Robotics in Manufacturing", "source": "Industry Today", "date": "2025-10-17"},
            {"title": "5G Networks Reach New Markets", "source": "Telecom News", "date": "2025-10-16"}
        ],
        "business": [
            {"title": "Global Markets Rally", "source": "Financial Times", "date": "2025-10-20"},
            {"title": "Startup Funding Reaches Record High", "source": "Entrepreneur", "date": "2025-10-19"},
            {"title": "Trade Agreements Boost Economy", "source": "Business Wire", "date": "2025-10-18"},
            {"title": "Corporate Sustainability Initiatives", "source": "Green Business", "date": "2025-10-17"},
            {"title": "E-commerce Trends 2025", "source": "Retail Today", "date": "2025-10-16"}
        ],
        "weather": [
            {"title": "Hurricane Season Updates", "source": "Weather Channel", "date": "2025-10-20"},
            {"title": "Climate Patterns Shift", "source": "Meteorology Today", "date": "2025-10-19"},
            {"title": "Record Temperatures in Europe", "source": "Global Weather", "date": "2025-10-18"},
            {"title": "Drought Conditions Improve", "source": "Climate News", "date": "2025-10-17"},
            {"title": "Winter Storm Preparations", "source": "Weather Service", "date": "2025-10-16"}
        ],
        "sports": [
            {"title": "Championship Finals Preview", "source": "Sports Network", "date": "2025-10-20"},
            {"title": "Olympic Qualifiers Begin", "source": "Athletic News", "date": "2025-10-19"},
            {"title": "Record-Breaking Performance", "source": "Sports Today", "date": "2025-10-18"},
            {"title": "Team Trades Shake Up League", "source": "Sports Insider", "date": "2025-10-17"},
            {"title": "Youth Sports Investment", "source": "Community Sports", "date": "2025-10-16"}
        ]
    }
    
    # Find matching category (case-insensitive)
    topic_lower = topic.lower()
    articles = None
    matched_topic = topic
    
    for category, article_list in news_database.items():
        if category in topic_lower or topic_lower in category:
            articles = article_list
            matched_topic = category.title()
            break
    
    # Default articles if topic not found
    if not articles:
        articles = [
            {"title": f"Latest Updates on {topic}", "source": "General News", "date": "2025-10-20"},
            {"title": f"{topic} Analysis", "source": "News Today", "date": "2025-10-19"},
            {"title": f"Expert Opinion on {topic}", "source": "Daily Review", "date": "2025-10-18"}
        ]
    
    # Limit to max_articles
    articles = articles[:max_articles]
    
    # Build response JSON
    response = {
        "topic": matched_topic,
        "article_count": len(articles),
        "articles": [
            {
                "title": article["title"],
                "source": article["source"],
                "published_date": article["date"],
                "summary": f"Article about {matched_topic.lower()}"
            }
            for article in articles
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return json.dumps(response)


# Export all functions for evaluation
__all__ = ['get_weather', 'get_news_articles']
