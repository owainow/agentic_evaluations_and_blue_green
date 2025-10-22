"""
Function definitions for AI Agent evaluation
These functions are provided to the evaluation framework for tool calling
"""

import json
from datetime import datetime

def get_weather(location: str, unit: str = "celsius") -> str:
    """
    Get current weather information for a specified location.
    
    Args:
        location: City name or location to get weather for
        unit: Temperature unit, either "celsius" or "fahrenheit" (default: "celsius")
    
    Returns:
        JSON string with weather information
    """
    # Mock weather data for testing
    weather_data = {
        "Seattle": {"temp_c": 18, "temp_f": 64, "condition": "Cloudy", "humidity": 75, "wind": 15},
        "Tokyo": {"temp_c": 22, "temp_f": 72, "condition": "Sunny", "humidity": 60, "wind": 10},
        "London": {"temp_c": 12, "temp_f": 54, "condition": "Rainy", "humidity": 85, "wind": 20},
        "Paris": {"temp_c": 15, "temp_f": 59, "condition": "Partly Cloudy", "humidity": 70, "wind": 12},
        "Sydney": {"temp_c": 25, "temp_f": 77, "condition": "Sunny", "humidity": 55, "wind": 8},
    }
    
    # Find matching city (case-insensitive, partial match)
    location_lower = location.lower()
    data = None
    matched_city = location
    
    for city, city_data in weather_data.items():
        if city.lower() in location_lower or location_lower in city.lower():
            data = city_data
            matched_city = city
            break
    
    # Default data if city not found
    if data is None:
        data = {"temp_c": 20, "temp_f": 68, "condition": "Unknown", "humidity": 65, "wind": 10}
    
    # Select temperature based on unit
    temperature = data["temp_c"] if unit.lower() == "celsius" else data["temp_f"]
    temp_unit = "celsius" if unit.lower() == "celsius" else "fahrenheit"
    
    # Build JSON response
    response = {
        "location": matched_city,
        "temperature": temperature,
        "temperature_unit": temp_unit,
        "condition": data["condition"],
        "humidity_percent": data["humidity"],
        "wind_speed_kmh": data["wind"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return json.dumps(response)


def get_news_articles(topic: str, max_articles: int = 5) -> str:
    """
    Get recent news articles for a specified topic.
    
    Args:
        topic: News topic or category to search for
        max_articles: Maximum number of articles to return (default: 5)
    
    Returns:
        JSON string with news articles
    """
    # Mock news data for testing
    news_data = {
        "technology": [
            {"title": "AI Breakthrough in Healthcare", "source": "Tech News", "date": "2025-10-20", "summary": "New AI system shows 95% accuracy in early disease detection."},
            {"title": "Quantum Computing Milestone Reached", "source": "Science Daily", "date": "2025-10-19", "summary": "Researchers achieve quantum supremacy in new experiment."},
            {"title": "5G Networks Expand Globally", "source": "Tech World", "date": "2025-10-18", "summary": "5G coverage reaches 60% of global population."},
            {"title": "Cybersecurity Threats Rise", "source": "Security Watch", "date": "2025-10-17", "summary": "New malware variants target cloud infrastructure."},
            {"title": "Green Tech Innovation Accelerates", "source": "Eco Tech", "date": "2025-10-16", "summary": "Solar panel efficiency reaches new record."},
        ],
        "business": [
            {"title": "Stock Markets Hit New Highs", "source": "Financial Times", "date": "2025-10-20", "summary": "Major indices reach record levels amid economic optimism."},
            {"title": "Startup Funding Surges", "source": "Business Insider", "date": "2025-10-19", "summary": "VC investments up 40% year-over-year."},
            {"title": "Supply Chain Disruptions Ease", "source": "Trade Journal", "date": "2025-10-18", "summary": "Global logistics returning to pre-pandemic levels."},
            {"title": "Corporate ESG Focus Grows", "source": "Business Weekly", "date": "2025-10-17", "summary": "Companies increase sustainability commitments."},
            {"title": "Remote Work Trends Continue", "source": "Work Today", "date": "2025-10-16", "summary": "70% of companies adopt hybrid work models."},
        ],
        "science": [
            {"title": "Mars Mission Makes Discovery", "source": "Space News", "date": "2025-10-20", "summary": "Rover finds evidence of ancient water on Mars."},
            {"title": "Cancer Treatment Breakthrough", "source": "Medical Journal", "date": "2025-10-19", "summary": "New immunotherapy shows promising results."},
            {"title": "Climate Data Shows Worrying Trends", "source": "Nature", "date": "2025-10-18", "summary": "Arctic ice loss accelerates beyond predictions."},
            {"title": "Gene Editing Advances", "source": "Biotech News", "date": "2025-10-17", "summary": "CRISPR technique refined for precision medicine."},
            {"title": "Ocean Exploration Reveals New Species", "source": "Marine Biology", "date": "2025-10-16", "summary": "Deep sea expedition discovers 20 new species."},
        ],
        "weather": [
            {"title": "Hurricane Season Update", "source": "Weather Channel", "date": "2025-10-20", "summary": "Tropical systems monitored in Atlantic basin."},
            {"title": "Record Temperatures in Europe", "source": "Climate News", "date": "2025-10-19", "summary": "Heatwave affects southern European regions."},
            {"title": "Severe Storms Expected", "source": "Storm Watch", "date": "2025-10-18", "summary": "Tornado warnings issued for midwest states."},
            {"title": "Drought Conditions Worsen", "source": "Agricultural News", "date": "2025-10-17", "summary": "Water restrictions implemented in western regions."},
            {"title": "Winter Forecast Released", "source": "Meteorology Today", "date": "2025-10-16", "summary": "La Niña pattern expected to influence winter weather."},
        ],
    }
    
    # Find matching topic (case-insensitive, partial match)
    topic_lower = topic.lower()
    articles = []
    matched_topic = topic
    
    for category, category_articles in news_data.items():
        if category in topic_lower or topic_lower in category:
            articles = category_articles
            matched_topic = category.title()
            break
    
    # Default to technology if no match
    if not articles:
        articles = news_data["technology"]
        matched_topic = "General"
    
    # Limit articles
    articles = articles[:max_articles]
    
    # Build JSON response
    response = {
        "topic": matched_topic,
        "article_count": len(articles),
        "articles": articles,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return json.dumps(response)
