# analyzers/solar_wind.py

import numpy as np
from datetime import datetime
import asyncio
import asyncio.events
from typing import Dict, List, Optional
import aiohttp
from scipy import stats

class SolarWindAnalyzer:
    """Analyzer for solar wind data and its correlation with magnetic disturbances.
    
Usage:
    analyzer = SolarWindAnalyzer()
    solar_wind_data = await analyzer.fetch_solar_wind_data()
    correlations = analyzer.analyze_correlations(magnetic_data, solar_wind_data)
    events = analyzer.detect_solar_events(solar_wind_data)
"""
    
    def __init__(self):
        self.base_url = "https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json"
        
    async def fetch_solar_wind_data(self) -> Dict:
        """Fetch solar wind data from NOAA API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_solar_wind_data(data)
                    else:
                        raise ValueError(f"API error: {response.status}")
        except Exception as e:
            raise ConnectionError(f"Failed to fetch solar wind data: {str(e)}")

    def _process_solar_wind_data(self, raw_data: List) -> Dict:
        """Process raw solar wind data into structured format"""
        try:
            # Skip header row
            data = raw_data[1:]
            
            processed = {
                'datetime': [],
                'density': [],
                'speed': [],
                'temperature': []
            }
            
            for row in data:
                try:
                    timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                    
                    # Convert values to float, handling None and empty strings
                    density = float(row[1]) if row[1] and row[1] != 'null' else np.nan
                    speed = float(row[2]) if row[2] and row[2] != 'null' else np.nan
                    temp = float(row[3]) if row[3] and row[3] != 'null' else np.nan
                    
                    processed['datetime'].append(timestamp)
                    processed['density'].append(density)
                    processed['speed'].append(speed)
                    processed['temperature'].append(temp)
                except (ValueError, IndexError):
                    continue
                    
            return processed
        except Exception as e:
            raise ValueError(f"Failed to process solar wind data: {str(e)}")

    def analyze_correlations(self, mag_data: Dict, solar_wind: Dict) -> Dict:
        """Calculate correlations between magnetic and solar wind parameters"""
        correlations = {}
        
        # Align timestamps
        mag_times = np.array([datetime.strptime(t, '%Y-%m-%d %H:%M:%S') 
                            for t in mag_data['datetime']])
        solar_times = np.array(solar_wind['datetime'])
        
        # Find overlapping time period
        start_time = max(mag_times[0], solar_times[0])
        end_time = min(mag_times[-1], solar_times[-1])
        
        # Filter data to overlapping period
        mag_mask = (mag_times >= start_time) & (mag_times <= end_time)
        solar_mask = (solar_times >= start_time) & (solar_times <= end_time)
        
        # Calculate correlations for each magnetic component
        for comp in ['H', 'D', 'Z']:
            if comp in mag_data:
                mag_values = np.array([float(x) if x is not None else np.nan 
                                     for x in mag_data[comp]])[mag_mask]
                
                for param in ['density', 'speed', 'temperature']:
                    solar_values = np.array(solar_wind[param])[solar_mask]
                    
                    # Interpolate to match timestamps if needed
                    if len(mag_values) != len(solar_values):
                        # Use simple linear interpolation
                        solar_values = np.interp(
                            np.arange(len(mag_values)),
                            np.linspace(0, len(mag_values), len(solar_values)),
                            solar_values
                        )
                    
                    # Calculate correlation coefficient
                    corr, p_value = stats.pearsonr(
                        mag_values[~np.isnan(mag_values)],
                        solar_values[~np.isnan(mag_values)]
                    )
                    
                    correlations[f"{comp}_{param}"] = {
                        'correlation': corr,
                        'p_value': p_value
                    }
        
        return correlations

    def detect_solar_events(self, solar_wind: Dict) -> List[Dict]:
        """Detect significant solar wind events"""
        events = []
        
        # Calculate rolling statistics
        window = 12  # 1-hour window (5-minute data)
        density = np.array(solar_wind['density'])
        speed = np.array(solar_wind['speed'])
        temperature = np.array(solar_wind['temperature'])
        
        # Define thresholds
        density_threshold = np.nanmean(density) + 2 * np.nanstd(density)
        speed_threshold = 500  # km/s
        temp_threshold = np.nanmean(temperature) + 2 * np.nanstd(temperature)
        
        for i in range(len(solar_wind['datetime'])):
            event_type = []
            
            # Check density
            if density[i] > density_threshold:
                event_type.append('High Density')
                
            # Check speed
            if speed[i] > speed_threshold:
                event_type.append('High Speed')
                
            # Check temperature
            if temperature[i] > temp_threshold:
                event_type.append('High Temperature')
                
            if event_type:
                events.append({
                    'time': solar_wind['datetime'][i],
                    'types': event_type,
                    'density': density[i],
                    'speed': speed[i],
                    'temperature': temperature[i]
                })
        
        return events