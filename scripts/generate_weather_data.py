#!/usr/bin/env python3
"""
Generate simulated historical weather data and save as PDF documents.
Creates realistic weather patterns for different cities and time periods.
"""

import random
import datetime
import math
from pathlib import Path
from typing import List, Dict, Tuple
import json

# Import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    print("ReportLab imported successfully")
except ImportError:
    print("ReportLab not found. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

class WeatherDataGenerator:
    def __init__(self):
        self.cities = {
            "Seattle": {
                "lat": 47.6062, "lon": -122.3321,
                "temp_base": 50, "temp_range": 25,
                "rain_prob": 0.4, "rain_base": 0.1
            },
            "Phoenix": {
                "lat": 33.4484, "lon": -112.0740,
                "temp_base": 75, "temp_range": 35,
                "rain_prob": 0.1, "rain_base": 0.05
            },
            "Miami": {
                "lat": 25.7617, "lon": -80.1918,
                "temp_base": 78, "temp_range": 15,
                "rain_prob": 0.3, "rain_base": 0.15
            },
            "Denver": {
                "lat": 39.7392, "lon": -104.9903,
                "temp_base": 55, "temp_range": 30,
                "rain_prob": 0.25, "rain_base": 0.08
            },
            "New_York": {
                "lat": 40.7128, "lon": -74.0060,
                "temp_base": 60, "temp_range": 28,
                "rain_prob": 0.3, "rain_base": 0.12
            }
        }
        
        self.weather_conditions = [
            "Clear", "Partly Cloudy", "Cloudy", "Light Rain", 
            "Heavy Rain", "Thunderstorm", "Snow", "Fog"
        ]
    
    def generate_seasonal_temp_adjustment(self, day_of_year: int, temp_range: float) -> float:
        """Generate seasonal temperature adjustment based on day of year."""
        # Peak summer around day 172 (June 21), peak winter around day 355 (December 21)
        seasonal_cycle = math.cos((day_of_year - 172) * 2 * math.pi / 365)
        return seasonal_cycle * temp_range * 0.7
    
    def generate_daily_weather(self, city: str, date: datetime.date) -> Dict:
        """Generate weather data for a specific city and date."""
        city_config = self.cities[city]
        day_of_year = date.timetuple().tm_yday
        
        # Base temperature with seasonal adjustment
        seasonal_adj = self.generate_seasonal_temp_adjustment(day_of_year, city_config["temp_range"])
        base_temp = city_config["temp_base"] + seasonal_adj
        
        # Daily temperature variation
        high_temp = base_temp + random.uniform(5, 15)
        low_temp = base_temp - random.uniform(5, 15)
        
        # Precipitation
        will_rain = random.random() < city_config["rain_prob"]
        precipitation = 0.0
        if will_rain:
            precipitation = random.uniform(0.01, city_config["rain_base"] * 10)
        
        # Wind speed and direction
        wind_speed = random.uniform(0, 25)
        wind_direction = random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
        
        # Humidity
        humidity = random.uniform(30, 90)
        
        # Weather condition
        if precipitation > 0.5:
            condition = random.choice(["Heavy Rain", "Thunderstorm"])
        elif precipitation > 0.1:
            condition = "Light Rain"
        elif humidity > 80:
            condition = random.choice(["Cloudy", "Fog"])
        else:
            condition = random.choice(["Clear", "Partly Cloudy", "Cloudy"])
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "city": city.replace("_", " "),
            "high_temp": round(high_temp, 1),
            "low_temp": round(low_temp, 1),
            "precipitation": round(precipitation, 2),
            "humidity": round(humidity, 1),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": wind_direction,
            "condition": condition
        }
    
    def generate_weather_summary(self, city: str, year: int, weather_data: List[Dict]) -> str:
        """Generate a weather summary for the year."""
        avg_high = sum(d["high_temp"] for d in weather_data) / len(weather_data)
        avg_low = sum(d["low_temp"] for d in weather_data) / len(weather_data)
        total_precipitation = sum(d["precipitation"] for d in weather_data)
        rainy_days = len([d for d in weather_data if d["precipitation"] > 0])
        
        # Find extremes
        hottest_day = max(weather_data, key=lambda x: x["high_temp"])
        coldest_day = min(weather_data, key=lambda x: x["low_temp"])
        wettest_day = max(weather_data, key=lambda x: x["precipitation"])
        
        summary = f"""
        <b>Weather Summary for {city.replace('_', ' ')} - {year}</b><br/><br/>
        
        <b>Temperature Statistics:</b><br/>
        • Average High Temperature: {avg_high:.1f}°F<br/>
        • Average Low Temperature: {avg_low:.1f}°F<br/>
        • Hottest Day: {hottest_day['date']} ({hottest_day['high_temp']}°F)<br/>
        • Coldest Day: {coldest_day['date']} ({coldest_day['low_temp']}°F)<br/><br/>
        
        <b>Precipitation Statistics:</b><br/>
        • Total Annual Precipitation: {total_precipitation:.2f} inches<br/>
        • Rainy Days: {rainy_days} days<br/>
        • Wettest Day: {wettest_day['date']} ({wettest_day['precipitation']:.2f} inches)<br/><br/>
        
        <b>Notable Weather Patterns:</b><br/>
        • Summer months showed typical seasonal warming patterns<br/>
        • Winter precipitation was {'above' if total_precipitation > 30 else 'below'} average<br/>
        • Wind patterns were consistent with regional climate norms<br/>
        """
        return summary
    
    def create_weather_pdf(self, city: str, year: int, output_dir: Path):
        """Create a PDF document with weather data for a city and year."""
        # Generate weather data for the year
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)
        
        weather_data = []
        current_date = start_date
        while current_date <= end_date:
            weather_data.append(self.generate_daily_weather(city, current_date))
            current_date += datetime.timedelta(days=1)
        
        # Create PDF
        filename = f"weather_data_{city}_{year}.pdf"
        filepath = output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Build the document
        story = []
        
        # Title
        title = f"Historical Weather Data - {city.replace('_', ' ')} ({year})"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Summary
        summary = self.generate_weather_summary(city, year, weather_data)
        story.append(Paragraph(summary, styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Monthly breakdown
        story.append(Paragraph("<b>Monthly Weather Data</b>", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Group data by month
        months = {}
        for data in weather_data:
            month_key = data["date"][:7]  # YYYY-MM
            if month_key not in months:
                months[month_key] = []
            months[month_key].append(data)
        
        # Create monthly summaries
        for month_key, month_data in months.items():
            month_name = datetime.datetime.strptime(month_key, "%Y-%m").strftime("%B %Y")
            
            avg_high = sum(d["high_temp"] for d in month_data) / len(month_data)
            avg_low = sum(d["low_temp"] for d in month_data) / len(month_data)
            total_precip = sum(d["precipitation"] for d in month_data)
            rainy_days = len([d for d in month_data if d["precipitation"] > 0])
            
            month_summary = f"""
            <b>{month_name}</b><br/>
            Average High: {avg_high:.1f}°F | Average Low: {avg_low:.1f}°F<br/>
            Total Precipitation: {total_precip:.2f}" | Rainy Days: {rainy_days}<br/>
            """
            
            story.append(Paragraph(month_summary, styles['Normal']))
            story.append(Spacer(1, 6))
        
        # Sample daily data table (first 10 days)
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Sample Daily Data (First 10 Days)</b>", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Create table data
        table_data = [
            ["Date", "High °F", "Low °F", "Precip \"", "Humidity %", "Wind", "Condition"]
        ]
        
        for data in weather_data[:10]:
            table_data.append([
                data["date"],
                f"{data['high_temp']:.1f}",
                f"{data['low_temp']:.1f}",
                f"{data['precipitation']:.2f}",
                f"{data['humidity']:.1f}",
                f"{data['wind_speed']:.1f} {data['wind_direction']}",
                data["condition"]
            ])
        
        # Create and style table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        print(f"Generated weather data PDF: {filepath}")
        
        return filepath

def main():
    """Generate weather data PDFs for multiple cities and years."""
    generator = WeatherDataGenerator()
    
    # Create output directory
    output_dir = Path("data/weather_pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data for multiple cities and years
    cities = ["Seattle", "Phoenix", "Miami", "Denver", "New_York"]
    years = [2021, 2022, 2023, 2024]
    
    print("Generating historical weather data PDFs...")
    
    generated_files = []
    for city in cities:
        for year in years:
            try:
                filepath = generator.create_weather_pdf(city, year, output_dir)
                generated_files.append(filepath)
            except Exception as e:
                print(f"Error generating weather data for {city} {year}: {e}")
    
    print(f"\nGenerated {len(generated_files)} weather data PDF files:")
    for filepath in generated_files:
        print(f"  - {filepath}")
    
    # Save a metadata file
    metadata = {
        "generated_at": datetime.datetime.now().isoformat(),
        "cities": cities,
        "years": years,
        "total_files": len(generated_files),
        "description": "Historical weather data for various US cities covering temperature, precipitation, humidity, wind, and weather conditions"
    }
    
    metadata_file = output_dir / "weather_data_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nMetadata saved to: {metadata_file}")

if __name__ == "__main__":
    main()