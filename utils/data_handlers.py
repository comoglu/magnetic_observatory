# utils/data_handlers.py


from typing import Dict, List, Optional, Union
import numpy as np
from datetime import datetime
import aiohttp
import json

from magnetic_observatory.analyzers.orientation import OrientationAnalyzer
from magnetic_observatory.analyzers.quality import QualityAnalyzer
from magnetic_observatory.analyzers.disturbance import DisturbanceAnalyzer

class DataFetchHandler:
    """Handles fetching and initial processing of magnetic observatory data"""
    
    def __init__(self, station_code: str):
        self.station_code = station_code
        self.base_url = "https://imag-data.bgs.ac.uk/GIN_V1/GINServices"
        
    async def fetch_data(self, params: Dict) -> Dict:
        """Fetch data from INTERMAGNET using aiohttp"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise ValueError(
                            f"Server error {response.status}: {error_text}"
                        )
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid data received: {str(e)}")

    async def fetch_kp_index(self) -> List[Dict]:
        """Fetch Kp index from NOAA using aiohttp"""
        try:
            url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except Exception:
            return []  # Silent fail for Kp index as it's non-critical

class DataProcessor:
    """Processes and transforms magnetic observatory data"""
    
    def __init__(self, data: Dict, station_code: str):
        self.data = data
        self.station_code = station_code
        self.orientation_analyzer = OrientationAnalyzer(data, station_code)
        self.quality_analyzer = QualityAnalyzer(data, station_code)
        self.disturbance_analyzer = DisturbanceAnalyzer(data, station_code)

    # In DataProcessor class:
    def process_data(self) -> Dict:
        """Process raw data and apply necessary transformations"""
        processed_data = self.data.copy()
        print("Available components:", list(processed_data.keys()))
        
        # Convert timestamps
        if 'datetime' in processed_data:
            processed_data['datetime'] = [
                self._normalize_timestamp(t) for t in processed_data['datetime']
            ]
                
        # Handle orientation conversions if needed
        try:
            orientation = self._detect_orientation()
            print(f"Detected orientation: {orientation}")
            
            if orientation == 'XYZ':
                hdz_data = self.orientation_analyzer.convert_xyz_to_hdz()
                processed_data.update(hdz_data)
                
            # Calculate S from HDZ components if entire S column is empty
            if 'S' in processed_data and all(s is None for s in processed_data['S']):
                print("Calculating S component...")
                if 'H' in processed_data and 'Z' in processed_data:
                    h = np.array([float(h) if h is not None else np.nan for h in processed_data['H']])
                    z = np.array([float(z) if z is not None else np.nan for z in processed_data['Z']])
                    print("H range:", np.nanmin(h), "-", np.nanmax(h))
                    print("Z range:", np.nanmin(z), "-", np.nanmax(z))
                    total_intensity = np.sqrt(h**2 + z**2)
                    processed_data['S'] = total_intensity.tolist()
                    print("S calculation successful")
                else:
                    print("Missing required components for S calculation")
                    
        except Exception as e:
            print(f"Error in data processing: {str(e)}")
            import traceback
            traceback.print_exc()
                
        return processed_data

    def validate_data(self) -> List[str]:
        """Validate data quality and return any warnings"""
        warnings = []
        
        # Check for data gaps
        gaps = self.quality_analyzer.analyze_data_gaps()
        if gaps:
            warnings.append(f"Found {len(gaps)} data gaps")
            
        # Check orientation consistency
        valid, message = self.orientation_analyzer.validate_orientation()
        if not valid:
            warnings.append(f"Orientation issue: {message}")
            
        return warnings

    def analyze_disturbances(self) -> Dict:
        """Analyze magnetic disturbances in the data"""
        return {
            'sudden_commencements': self.disturbance_analyzer.detect_sudden_commencements(),
            'substorms': self.disturbance_analyzer.detect_substorms(),
            'k_indices': self.disturbance_analyzer.calculate_k_index(),
            'disturbed_periods': self.disturbance_analyzer.find_disturbed_periods()
        }

    def _normalize_timestamp(self, timestamp: str) -> str:
        """Normalize timestamp format"""
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def _detect_orientation(self) -> str:
        """Detect data orientation"""
        xyz = all(comp in self.data for comp in ['X', 'Y', 'Z'])
        hdz = all(comp in self.data for comp in ['H', 'D', 'Z'])
        
        if xyz and not hdz:
            return 'XYZ'
        elif hdz and not xyz:
            return 'HDZ'
        else:
            return 'UNKNOWN'

class ExportHandler:
    """Handles data export operations"""
    
    @staticmethod
    def to_csv(data: Dict, filename: str):
        """Export data to CSV format"""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            headers = ['Time'] + list(data.keys() - {'datetime'})
            writer.writerow(headers)
            
            for i, timestamp in enumerate(data['datetime']):
                row = [timestamp]
                for key in headers[1:]:
                    value = data[key][i] if i < len(data[key]) else None
                    row.append(value)
                writer.writerow(row)

    @staticmethod
    def to_excel(data: Dict, filename: str):
        """Export data to Excel format"""
        import xlsxwriter
        
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        
        # Write headers
        headers = ['Time'] + list(data.keys() - {'datetime'})
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Write data
        for row, timestamp in enumerate(data['datetime'], 1):
            worksheet.write(row, 0, timestamp)
            for col, key in enumerate(headers[1:], 1):
                if row <= len(data[key]):
                    value = data[key][row-1]
                    if value is not None:
                        worksheet.write(row, col, value)
        
        workbook.close()
