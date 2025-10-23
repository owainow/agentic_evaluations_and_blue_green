import azure.functions as func
import logging
import json
import time
from datetime import datetime
from typing import Optional

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Configure logging for better monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route(route="get_weather", methods=["GET", "POST"])
def get_weather(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get current weather information for a location.
    This is a mock function that returns simulated weather data.
    
    Parameters:
    - location: City name or location identifier
    - unit: Temperature unit ('celsius' or 'fahrenheit')
    """
    start_time = time.time()
    correlation_id = req.headers.get('x-correlation-id', 'unknown')
    
    logger.info(f'Weather function triggered. Correlation ID: {correlation_id}')
    
    try:
        # Get parameters from query string or JSON body
        if req.method == "GET":
            location = req.params.get('location')
            unit = req.params.get('unit', 'celsius')
        else:  # POST
            try:
                req_body = req.get_json()
                location = req_body.get('location') if req_body else None
                unit = req_body.get('unit', 'celsius') if req_body else 'celsius'
            except ValueError as e:
                logger.warning(f'Failed to parse JSON body: {e}. Correlation ID: {correlation_id}')
                location = req.params.get('location')
                unit = req.params.get('unit', 'celsius')
        
        logger.info(f'Weather request - Location: {location}, Unit: {unit}, Method: {req.method}, Correlation ID: {correlation_id}')
        
        if not location:
            logger.error(f'Missing required parameter: location. Correlation ID: {correlation_id}')
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameter: location"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Mock weather data for various cities
        weather_data = {
            "seattle": {"temp_c": 18, "condition": "Cloudy", "humidity": 75, "wind": 15},
            "tokyo": {"temp_c": 22, "condition": "Sunny", "humidity": 60, "wind": 10},
            "london": {"temp_c": 12, "condition": "Rainy", "humidity": 85, "wind": 20},
            "new york": {"temp_c": 20, "condition": "Partly Cloudy", "humidity": 70, "wind": 12},
            "paris": {"temp_c": 15, "condition": "Overcast", "humidity": 80, "wind": 8}
        }
        
        # Find matching city (case-insensitive, partial match)
        location_lower = location.lower()
        matched_city = None
        matched_data = None
        
        for city, data in weather_data.items():
            if city in location_lower or location_lower in city:
                matched_city = city.title()
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
        
        execution_time = time.time() - start_time
        logger.info(f'Weather data returned for {location} in {execution_time:.3f}s. Correlation ID: {correlation_id}')
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json",
            headers={"x-correlation-id": correlation_id}
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f'Weather function error: {str(e)}. Execution time: {execution_time:.3f}s. Correlation ID: {correlation_id}')
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }),
            status_code=500,
            mimetype="application/json",
            headers={"x-correlation-id": correlation_id}
        )


@app.route(route="get_news_articles", methods=["GET", "POST"])
def get_news_articles(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get recent news articles for a given topic.
    This is a mock function that returns simulated news data.
    
    Parameters:
    - topic: News topic or category
    - max_articles: Maximum number of articles to return (default: 5)
    """
    start_time = time.time()
    correlation_id = req.headers.get('x-correlation-id', 'unknown')
    
    logger.info(f'News articles function triggered. Correlation ID: {correlation_id}')
    
    try:
        # Get parameters from query string or JSON body
        if req.method == "GET":
            topic = req.params.get('topic')
            max_articles = int(req.params.get('max_articles', 5))
        else:  # POST
            try:
                req_body = req.get_json()
                topic = req_body.get('topic') if req_body else None
                max_articles = int(req_body.get('max_articles', 5)) if req_body else 5
            except ValueError as e:
                logger.warning(f'Failed to parse JSON body: {e}. Correlation ID: {correlation_id}')
                topic = req.params.get('topic')
                max_articles = int(req.params.get('max_articles', 5))
        
        logger.info(f'News request - Topic: {topic}, Max articles: {max_articles}, Method: {req.method}, Correlation ID: {correlation_id}')
        
        if not topic:
            logger.error(f'Missing required parameter: topic. Correlation ID: {correlation_id}')
            return func.HttpResponse(
                json.dumps({"error": "Missing required parameter: topic"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Mock news data by category
        news_database = {
            "technology": [
                {"title": "AI Breakthrough in Healthcare", "source": "Tech News", "date": "2025-10-22"},
                {"title": "New Quantum Computing Milestone", "source": "Science Daily", "date": "2025-10-21"},
                {"title": "Cloud Services Expand Globally", "source": "Business Tech", "date": "2025-10-20"},
                {"title": "Robotics in Manufacturing", "source": "Industry Today", "date": "2025-10-19"},
                {"title": "5G Networks Reach New Markets", "source": "Telecom News", "date": "2025-10-18"}
            ],
            "business": [
                {"title": "Global Markets Rally", "source": "Financial Times", "date": "2025-10-22"},
                {"title": "Startup Funding Reaches Record High", "source": "Entrepreneur", "date": "2025-10-21"},
                {"title": "Trade Agreements Boost Economy", "source": "Business Wire", "date": "2025-10-20"},
                {"title": "Corporate Sustainability Initiatives", "source": "Green Business", "date": "2025-10-19"},
                {"title": "E-commerce Trends 2025", "source": "Retail Today", "date": "2025-10-18"}
            ],
            "weather": [
                {"title": "Hurricane Season Updates", "source": "Weather Channel", "date": "2025-10-22"},
                {"title": "Climate Patterns Shift", "source": "Meteorology Today", "date": "2025-10-21"},
                {"title": "Record Temperatures in Europe", "source": "Global Weather", "date": "2025-10-20"},
                {"title": "Drought Conditions Improve", "source": "Climate News", "date": "2025-10-19"},
                {"title": "Winter Storm Preparations", "source": "Weather Service", "date": "2025-10-18"}
            ],
            "sports": [
                {"title": "Championship Finals Preview", "source": "Sports Network", "date": "2025-10-22"},
                {"title": "Olympic Qualifiers Begin", "source": "Athletic News", "date": "2025-10-21"},
                {"title": "Record-Breaking Performance", "source": "Sports Today", "date": "2025-10-20"},
                {"title": "Team Trades Shake Up League", "source": "Sports Insider", "date": "2025-10-19"},
                {"title": "Youth Sports Investment", "source": "Community Sports", "date": "2025-10-18"}
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
                {"title": f"Latest Updates on {topic}", "source": "General News", "date": "2025-10-22"},
                {"title": f"{topic} Analysis", "source": "News Today", "date": "2025-10-21"},
                {"title": f"Expert Opinion on {topic}", "source": "Daily Review", "date": "2025-10-20"}
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
        
        execution_time = time.time() - start_time
        logger.info(f'News articles returned for topic: {topic} in {execution_time:.3f}s. Correlation ID: {correlation_id}')
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json",
            headers={"x-correlation-id": correlation_id}
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f'News function error: {str(e)}. Execution time: {execution_time:.3f}s. Correlation ID: {correlation_id}')
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }),
            status_code=500,
            mimetype="application/json",
            headers={"x-correlation-id": correlation_id}
        )