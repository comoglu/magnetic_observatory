# analyzers/base_analyzer.py

from typing import Dict, List, Optional, Union
import numpy as np
from datetime import datetime
from ..utils.constants import STATION_INFO, QC_PARAMS

class BaseAnalyzer:
    def __init__(self, data: Dict[str, List], station_code: str):
        self.data = data
        self.station_code = station_code
        self.station_info = STATION_INFO.get(station_code, {})
        self._validate_data()
        
    def _validate_data(self) -> bool:
        """Enhanced data validation"""
        required_fields = ['datetime']
        
        # Check for empty or None data
        if not self.data:
            raise ValueError("Empty dataset")
        
        # Check required fields
        if not all(field in self.data for field in required_fields):
            raise ValueError("Missing required fields in data")
        
        # Check datetime field
        if not self.data['datetime'] or all(x is None for x in self.data['datetime']):
            raise ValueError("No valid datetime entries")
        
        return True

    def get_component_data(self, component: str) -> np.ndarray:
        """Safely get component data as numpy array with robust NaN handling"""
        if component not in self.data:
            raise ValueError(f"Component {component} not found in data")
        
        values = self.data[component]
        
        # Handle various null/empty scenarios
        if not values or all(x is None for x in values):
            raise ValueError(f"No valid data for component {component}")
        
        return np.array([float(x) if x is not None else np.nan for x in values])
        
    def get_datetime_array(self) -> np.ndarray:
        """Convert datetime strings to numpy datetime64 array"""
        return np.array([np.datetime64(t.replace('Z', '+00:00')) 
                        for t in self.data['datetime']])
                        
    def get_available_components(self) -> List[str]:
        """Get list of available components in the data"""
        return [k for k in self.data.keys() 
                if k not in ['datetime'] and isinstance(self.data[k], list)]