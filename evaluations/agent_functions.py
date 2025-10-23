#!/usr/bin/env python3
"""
Function implementations for AI Agent evaluations
These functions are called by the microsoft/ai-agent-evals GitHub Action
"""
import os
import json
import requests
from datetime import datetime, timezone


def get_weather(location: str, unit: str = "celsius") -> str:
    """
    Fetches the current weather for a specified location.
    This function calls the Azure Function or provides mock data for evaluation.
    
    :param location: The city and state/country, e.g. 'Seattle, WA' or 'London, UK'
    :param unit: Temperature unit - 'celsius' or 'fahrenheit'
    :return: Weather information as a JSON string with standardized format
    """
    function_app_url = os.getenv('FUNCTION_APP_URL')
    
    if function_app_url:
        # Call the Azure Function
        try:
            url = f"{function_app_url}/api/get_weather"
            params = {"location": location, "unit": unit}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            print(f"Warning: Azure Function call failed: {e}. Using mock data.")
    
    # Fallback to mock data for evaluation
    mock_data = {
        "location": location,
        "temperature": 22.0 if unit == "celsius" else 72.0,
        "temperature_unit": unit,
        "condition": "Partly Cloudy",
        "humidity_percent": 65,
        "wind_speed_kmh": 15,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return json.dumps({"response": mock_data})


def get_news_articles(topic: str, max_articles: int = 5) -> str:
    """
    Fetches news articles for a specified topic.
    This function calls the Azure Function or provides mock data for evaluation.
    
    :param topic: The news topic to search for
    :param max_articles: Maximum number of articles to return
    :return: News articles as a JSON string
    """
    function_app_url = os.getenv('FUNCTION_APP_URL')
    
    if function_app_url:
        # Call the Azure Function
        try:
            url = f"{function_app_url}/api/get_news_articles"
            params = {"topic": topic, "max_articles": max_articles}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            print(f"Warning: Azure Function call failed: {e}. Using mock data.")
    
    # Fallback to mock data for evaluation
    mock_articles = [
        {
            "title": f"Breaking: Latest {topic} developments",
            "summary": f"Important updates in the {topic} sector with significant implications.",
            "url": f"https://example.com/{topic}-news-1",
            "published_date": datetime.now(timezone.utc).isoformat(),
            "source": "News Source"
        },
        {
            "title": f"{topic.title()} market analysis",
            "summary": f"Expert analysis of current {topic} trends and future predictions.",
            "url": f"https://example.com/{topic}-news-2", 
            "published_date": datetime.now(timezone.utc).isoformat(),
            "source": "Market Watch"
        }
    ]
    
    # Limit articles to max_articles
    articles = mock_articles[:max_articles]
    
    mock_data = {
        "topic": topic,
        "articles": articles,
        "article_count": len(articles),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return json.dumps({"response": mock_data})