#!/usr/bin/env python3
"""
Generate simulated news articles and save as PDF documents.
Creates realistic news content covering weather events, climate topics, and seasonal reports.
"""

import random
import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import json

# Import PDF generation libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

class NewsDataGenerator:
    def __init__(self):
        self.news_topics = {
            "weather_events": [
                "Severe Thunderstorm Warning",
                "Winter Storm Advisory",
                "Heat Wave Impacts",
                "Flooding Concerns",
                "Drought Conditions",
                "Tornado Watch",
                "Hurricane Preparation",
                "Blizzard Recovery"
            ],
            "climate_science": [
                "Climate Change Research",
                "Seasonal Pattern Analysis",
                "Temperature Trend Study",
                "Precipitation Changes",
                "Weather Prediction Models",
                "Climate Adaptation",
                "Environmental Impact",
                "Weather Technology"
            ],
            "seasonal_reports": [
                "Spring Weather Outlook",
                "Summer Heat Forecast",
                "Fall Climate Preview",
                "Winter Weather Preparation",
                "Seasonal Allergies Update",
                "Holiday Weather Travel",
                "Back to School Weather",
                "Growing Season Report"
            ]
        }
        
        self.cities = [
            "Seattle", "Phoenix", "Miami", "Denver", "New York",
            "Los Angeles", "Chicago", "Houston", "Atlanta", "Boston"
        ]
        
        self.news_sources = [
            "National Weather Service",
            "Climate Research Institute",
            "Weather Channel News",
            "Environmental Science Daily",
            "Local Weather Network",
            "Meteorological Society",
            "Climate Action News",
            "Weather Watch Report"
        ]
        
        self.authors = [
            "Dr. Sarah Johnson", "Mike Weather", "Climate Reporter Lisa Chen",
            "Meteorologist Tom Smith", "Environmental Writer Alex Rodriguez",
            "Weather Analyst Jennifer Davis", "Dr. Michael Storm",
            "Climate Scientist Emma Wilson", "Weather Correspondent David Lee"
        ]
    
    def generate_weather_event_article(self, date: datetime.date) -> Dict:
        """Generate a weather event news article."""
        topic = random.choice(self.news_topics["weather_events"])
        city = random.choice(self.cities)
        source = random.choice(self.news_sources)
        author = random.choice(self.authors)
        
        # Generate weather-specific content based on topic
        if "Storm" in topic or "Thunderstorm" in topic:
            content = self._generate_storm_content(city, topic)
        elif "Heat" in topic or "Drought" in topic:
            content = self._generate_heat_content(city, topic)
        elif "Winter" in topic or "Blizzard" in topic:
            content = self._generate_winter_content(city, topic)
        elif "Flood" in topic:
            content = self._generate_flood_content(city, topic)
        else:
            content = self._generate_general_weather_content(city, topic)
        
        return {
            "title": f"{topic} Affects {city} Area",
            "author": author,
            "source": source,
            "date": date.strftime("%B %d, %Y"),
            "category": "Weather Events",
            "city": city,
            "content": content,
            "tags": ["weather", "forecast", city.lower(), topic.lower().replace(" ", "-")]
        }
    
    def generate_climate_science_article(self, date: datetime.date) -> Dict:
        """Generate a climate science news article."""
        topic = random.choice(self.news_topics["climate_science"])
        city = random.choice(self.cities)
        source = random.choice(self.news_sources)
        author = random.choice(self.authors)
        
        content = self._generate_climate_science_content(city, topic)
        
        return {
            "title": f"New Study: {topic} in {city} Region",
            "author": author,
            "source": source,
            "date": date.strftime("%B %d, %Y"),
            "category": "Climate Science",
            "city": city,
            "content": content,
            "tags": ["climate", "research", "science", city.lower(), "study"]
        }
    
    def generate_seasonal_report_article(self, date: datetime.date) -> Dict:
        """Generate a seasonal weather report article."""
        topic = random.choice(self.news_topics["seasonal_reports"])
        city = random.choice(self.cities)
        source = random.choice(self.news_sources)
        author = random.choice(self.authors)
        
        content = self._generate_seasonal_content(city, topic, date)
        
        return {
            "title": f"{topic}: {city} Regional Analysis",
            "author": author,
            "source": source,
            "date": date.strftime("%B %d, %Y"),
            "category": "Seasonal Reports",
            "city": city,
            "content": content,
            "tags": ["seasonal", "forecast", "outlook", city.lower()]
        }
    
    def _generate_storm_content(self, city: str, topic: str) -> str:
        """Generate storm-related article content."""
        wind_speed = random.randint(45, 85)
        rain_amount = random.uniform(1.5, 4.0)
        
        return f"""
        The National Weather Service has issued a {topic.lower()} for the {city} metropolitan area, 
        effective immediately through tomorrow evening. Meteorologists are tracking a powerful storm 
        system that is expected to bring damaging winds up to {wind_speed} mph and heavy rainfall 
        totaling {rain_amount:.1f} inches.
        
        Local emergency management officials are advising residents to secure outdoor furniture and 
        avoid unnecessary travel during peak storm hours. The storm is part of a larger weather 
        pattern affecting the region, with similar conditions reported in neighboring areas.
        
        Power outages are possible, and residents should prepare emergency kits with flashlights, 
        batteries, and non-perishable food. The storm is expected to move through the area between 
        {random.randint(6, 10)} PM today and {random.randint(6, 10)} AM tomorrow.
        
        Local meteorologist Dr. Weather stated, "This system shows the classic signature of a 
        {random.choice(['fast-moving', 'slow-moving', 'intensifying'])} storm that can produce 
        significant impacts in a short time frame. We're monitoring it closely."
        
        Updates will be provided as conditions develop. Residents are encouraged to monitor local 
        weather alerts and follow safety guidelines during severe weather events.
        """
    
    def _generate_heat_content(self, city: str, topic: str) -> str:
        """Generate heat/drought-related article content."""
        temp = random.randint(95, 115)
        days = random.randint(5, 14)
        
        return f"""
        Excessive heat warnings remain in effect for the {city} area as temperatures soar to 
        {temp}°F for the {days}th consecutive day. This extended period of extreme heat has 
        prompted health officials to open cooling centers throughout the metropolitan region.
        
        The heat wave is being caused by a persistent high-pressure system that has stalled 
        over the region, creating a heat dome effect. Overnight lows have only dropped to 
        {temp - random.randint(15, 25)}°F, providing little relief from the oppressive conditions.
        
        City health department officials report increased emergency room visits related to 
        heat exhaustion and dehydration. "We're seeing a significant uptick in heat-related 
        illnesses," said Public Health Director Sarah Martinez. "It's crucial that people 
        stay hydrated and seek air conditioning when possible."
        
        Energy companies are reporting record electricity demand as air conditioning usage 
        peaks. Rolling blackouts remain a possibility if demand continues to exceed supply 
        capacity during afternoon peak hours.
        
        The extended forecast suggests relief may come by {random.choice(['early next week', 'the weekend', 'midweek'])}, 
        when a cooler air mass is expected to move into the region. Until then, residents 
        should continue to take precautions against heat-related illness.
        """
    
    def _generate_winter_content(self, city: str, topic: str) -> str:
        """Generate winter weather article content."""
        snow_amount = random.randint(6, 18)
        temp = random.randint(-5, 25)
        
        return f"""
        A major winter storm is bearing down on the {city} region, with forecasters predicting 
        {snow_amount} inches of snow and temperatures dropping to {temp}°F. The storm is 
        expected to begin late tonight and continue through tomorrow afternoon.
        
        Transportation officials are pre-treating roads with salt and sand, and snow plows 
        are standing by. The city's emergency management director announced that all 
        non-essential city services will be suspended during the storm's peak intensity.
        
        School districts throughout the metropolitan area have already announced closures 
        for tomorrow, affecting over {random.randint(50000, 150000):,} students. Many 
        businesses are also allowing employees to work from home or closing early.
        
        The winter storm is part of a larger weather system moving across the region, 
        driven by arctic air masses colliding with warmer, moisture-laden air. Wind gusts 
        up to {random.randint(25, 45)} mph could create blizzard conditions and 
        significantly reduce visibility.
        
        Residents are advised to stock up on essential supplies including food, water, 
        medications, and heating fuel. Power outages are possible due to heavy snow 
        accumulation on power lines and strong winds.
        
        "This is shaping up to be one of the most significant winter storms we've seen 
        this season," said Chief Meteorologist Jennifer Snow. "People should avoid travel 
        unless absolutely necessary."
        """
    
    def _generate_flood_content(self, city: str, topic: str) -> str:
        """Generate flood-related article content."""
        rain_amount = random.uniform(3.0, 8.0)
        rivers = random.choice([
            "Blue River", "Clear Creek", "Mill River", "Stone Creek", "West Branch"
        ])
        
        return f"""
        Flash flood warnings have been issued for the {city} area following {rain_amount:.1f} 
        inches of rainfall in just {random.randint(2, 6)} hours. The {rivers} has risen to 
        near flood stage, prompting evacuations in low-lying areas.
        
        Emergency responders have conducted {random.randint(12, 35)} water rescues since 
        the flooding began, with several motorists becoming stranded in rapidly rising water. 
        "Turn Around, Don't Drown" remains the critical message from emergency officials.
        
        The heavy rainfall was produced by slow-moving thunderstorms that repeatedly passed 
        over the same areas. Weather radar showed training storms with rainfall rates 
        exceeding {random.uniform(1.5, 3.0):.1f} inches per hour during peak intensity.
        
        Several major roadways remain closed, including portions of Highway {random.randint(10, 99)} 
        and {random.choice(['Main Street', 'First Avenue', 'River Road', 'Oak Street'])}. 
        Commuters are advised to seek alternate routes and allow extra travel time.
        
        The Red Cross has opened emergency shelters for displaced residents, and utility 
        companies are monitoring infrastructure for potential impacts. Flood waters began 
        receding late this afternoon, but streets in the downtown area remain impassable.
        
        "The rapid onset of this flooding caught many people off guard," said Emergency 
        Management Coordinator Mike Johnson. "Climate change is making these intense 
        rainfall events more common and more dangerous."
        """
    
    def _generate_general_weather_content(self, city: str, topic: str) -> str:
        """Generate general weather article content."""
        return f"""
        The {city} area is currently experiencing {topic.lower()}, according to the latest 
        reports from the National Weather Service. Meteorologists are closely monitoring 
        the developing situation and providing regular updates to the public.
        
        Local conditions show {random.choice(['improving', 'deteriorating', 'variable'])} 
        trends with {random.choice(['clearing skies', 'increasing clouds', 'mixed conditions'])} 
        expected over the next {random.randint(24, 72)} hours.
        
        Temperature readings have been {random.choice(['above', 'below', 'near'])} normal 
        for this time of year, with current conditions reflecting broader regional weather 
        patterns. Wind speeds have been recorded at {random.randint(5, 25)} mph from the 
        {random.choice(['north', 'south', 'east', 'west', 'northeast', 'southwest'])}.
        
        Residents should continue to monitor weather conditions and follow any advisories 
        issued by local emergency management officials. The extended forecast suggests 
        {random.choice(['stable', 'changing', 'unsettled'])} conditions through the weekend.
        
        This weather event is part of larger seasonal patterns affecting the region, with 
        similar conditions reported in surrounding metropolitan areas. Local agriculture 
        and transportation sectors are monitoring the situation closely.
        """
    
    def _generate_climate_science_content(self, city: str, topic: str) -> str:
        """Generate climate science article content."""
        years = random.randint(15, 50)
        percentage = random.randint(10, 45)
        
        return f"""
        A comprehensive {years}-year study of {topic.lower()} in the {city} region has 
        revealed significant trends that could impact future weather patterns and community 
        planning efforts. The research, conducted by a team of climate scientists from 
        leading universities, analyzed decades of meteorological data.
        
        Key findings indicate that regional climate patterns have shifted by approximately 
        {percentage}% over the study period, with notable changes in seasonal temperature 
        and precipitation distributions. The data shows {random.choice(['warming', 'cooling', 'variable'])} 
        trends during {random.choice(['summer', 'winter', 'spring', 'fall'])} months.
        
        Dr. {random.choice(['Climate', 'Weather', 'Research', 'Science'])} Expert, lead 
        researcher on the project, explained: "These findings provide crucial insights into 
        how our local climate is evolving. Understanding these patterns helps us better 
        prepare for future weather events and adapt our infrastructure accordingly."
        
        The study utilized advanced statistical modeling and machine learning techniques 
        to identify patterns in temperature, precipitation, humidity, and wind data. 
        Researchers also incorporated satellite imagery and ground-based observations 
        to validate their findings.
        
        Implications for the {city} metropolitan area include potential changes to:
        • Seasonal weather patterns and timing
        • Extreme weather event frequency and intensity
        • Water resource management requirements
        • Urban planning and infrastructure design
        • Agricultural practices and growing seasons
        
        The research team recommends continued monitoring and adaptation strategies to 
        address these evolving climate conditions. The full study will be published in 
        the Journal of Regional Climate Science next month.
        
        Local government officials are reviewing the findings to inform future policy 
        decisions related to emergency preparedness, infrastructure investment, and 
        environmental protection measures.
        """
    
    def _generate_seasonal_content(self, city: str, topic: str, date: datetime.date) -> str:
        """Generate seasonal report article content."""
        month = date.month
        season = self._get_season(month)
        
        temp_range = f"{random.randint(45, 65)}-{random.randint(70, 90)}"
        precip_chance = random.randint(20, 60)
        
        return f"""
        The latest {season} weather outlook for the {city} metropolitan area indicates 
        {random.choice(['typical', 'above-normal', 'below-normal'])} conditions for the 
        upcoming period. Meteorologists have analyzed long-range forecast models to 
        provide residents with seasonal planning information.
        
        Temperature forecasts suggest daily highs will range from {temp_range}°F, which is 
        {random.choice(['slightly above', 'near', 'slightly below'])} the historical average 
        for this time of year. Overnight lows are expected to follow similar patterns.
        
        Precipitation outlook shows a {precip_chance}% chance of normal rainfall amounts, 
        with the possibility of {random.choice(['scattered', 'widespread', 'isolated'])} 
        {random.choice(['showers', 'thunderstorms', 'light rain'])} throughout the period.
        
        Key seasonal considerations for {city} residents include:
        
        • Weather patterns typical of {season} in the regional climate
        • {random.choice(['Increased', 'Decreased', 'Variable'])} storm activity compared to last year
        • Temperature variations affecting energy consumption
        • Outdoor activity planning recommendations
        • Garden and landscape care considerations
        
        The National Weather Service emphasizes that seasonal outlooks provide general 
        trends rather than specific daily forecasts. "These outlooks help people plan 
        for the months ahead, but daily weather can still vary significantly from the 
        overall seasonal pattern," explained Senior Meteorologist weather expert.
        
        Historical data shows that {season} weather in the {city} area has been 
        {random.choice(['generally stable', 'increasingly variable', 'trending warmer'])} 
        over the past decade. Climate factors including ocean temperatures and atmospheric 
        patterns continue to influence regional weather.
        
        Residents are encouraged to stay informed about weather conditions through 
        official National Weather Service forecasts and local emergency management 
        communications. Updates to the seasonal outlook will be provided monthly.
        """
    
    def _get_season(self, month: int) -> str:
        """Determine season based on month."""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
    
    def create_news_pdf(self, articles: List[Dict], date_range: str, output_dir: Path):
        """Create a PDF document with multiple news articles."""
        filename = f"weather_news_{date_range.replace(' ', '_').replace('-', '_')}.pdf"
        filepath = output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        article_title_style = ParagraphStyle(
            'ArticleTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=5
        )
        
        # Build the document
        story = []
        
        # Main title
        story.append(Paragraph(f"Weather and Climate News - {date_range}", title_style))
        story.append(Spacer(1, 12))
        
        # Table of contents
        story.append(Paragraph("<b>Featured Articles</b>", styles['Heading2']))
        for i, article in enumerate(articles, 1):
            story.append(Paragraph(f"{i}. {article['title']}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Articles
        for i, article in enumerate(articles, 1):
            # Article title
            story.append(Paragraph(f"Article {i}: {article['title']}", article_title_style))
            
            # Article metadata
            meta_text = f"By {article['author']} | {article['source']} | {article['date']} | Category: {article['category']}"
            story.append(Paragraph(meta_text, meta_style))
            story.append(Spacer(1, 8))
            
            # Article content
            # Clean up the content formatting
            content_lines = article['content'].strip().split('\n')
            cleaned_content = []
            for line in content_lines:
                line = line.strip()
                if line:
                    cleaned_content.append(line)
            
            content = ' '.join(cleaned_content)
            story.append(Paragraph(content, styles['Normal']))
            
            # Tags
            if article.get('tags'):
                tags_text = f"<i>Tags: {', '.join(article['tags'])}</i>"
                story.append(Spacer(1, 8))
                story.append(Paragraph(tags_text, meta_style))
            
            # Separator between articles
            if i < len(articles):
                story.append(Spacer(1, 20))
                story.append(Paragraph("─" * 80, meta_style))
                story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        print(f"Generated news PDF: {filepath}")
        
        return filepath

def main():
    """Generate news article PDFs for different time periods."""
    generator = NewsDataGenerator()
    
    # Create output directory
    output_dir = Path("data/news_pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating weather and climate news PDFs...")
    
    generated_files = []
    
    # Generate news for different quarters/periods
    periods = [
        ("Q1 2023", datetime.date(2023, 1, 1), datetime.date(2023, 3, 31)),
        ("Q2 2023", datetime.date(2023, 4, 1), datetime.date(2023, 6, 30)),
        ("Q3 2023", datetime.date(2023, 7, 1), datetime.date(2023, 9, 30)),
        ("Q4 2023", datetime.date(2023, 10, 1), datetime.date(2023, 12, 31)),
        ("Q1 2024", datetime.date(2024, 1, 1), datetime.date(2024, 3, 31)),
        ("Q2 2024", datetime.date(2024, 4, 1), datetime.date(2024, 6, 30)),
        ("Q3 2024", datetime.date(2024, 7, 1), datetime.date(2024, 9, 30)),
        ("Q4 2024", datetime.date(2024, 10, 1), datetime.date(2024, 12, 31))
    ]
    
    for period_name, start_date, end_date in periods:
        try:
            # Generate 8-12 articles per period
            num_articles = random.randint(8, 12)
            articles = []
            
            for _ in range(num_articles):
                # Random date within the period
                days_diff = (end_date - start_date).days
                random_days = random.randint(0, days_diff)
                article_date = start_date + datetime.timedelta(days=random_days)
                
                # Random article type
                article_type = random.choice([
                    "weather_event", "climate_science", "seasonal_report"
                ])
                
                if article_type == "weather_event":
                    article = generator.generate_weather_event_article(article_date)
                elif article_type == "climate_science":
                    article = generator.generate_climate_science_article(article_date)
                else:
                    article = generator.generate_seasonal_report_article(article_date)
                
                articles.append(article)
            
            # Sort articles by date
            articles.sort(key=lambda x: datetime.datetime.strptime(x['date'], "%B %d, %Y"))
            
            # Create PDF
            filepath = generator.create_news_pdf(articles, period_name, output_dir)
            generated_files.append(filepath)
            
        except Exception as e:
            print(f"Error generating news for {period_name}: {e}")
    
    print(f"\nGenerated {len(generated_files)} news PDF files:")
    for filepath in generated_files:
        print(f"  - {filepath}")
    
    # Save metadata
    metadata = {
        "generated_at": datetime.datetime.now().isoformat(),
        "periods": [p[0] for p in periods],
        "total_files": len(generated_files),
        "description": "Simulated weather and climate news articles covering various topics including severe weather events, climate science research, and seasonal forecasts"
    }
    
    metadata_file = output_dir / "news_data_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nMetadata saved to: {metadata_file}")

if __name__ == "__main__":
    main()