# analyzers/orientation.py

import numpy as np
from typing import Dict, List, Tuple
from .base_analyzer import BaseAnalyzer

class OrientationAnalyzer(BaseAnalyzer):
    def convert_xyz_to_hdz(self) -> Dict[str, List[float]]:
        """Convert XYZ components to HDZ"""
        try:
            x = self.get_component_data('X')
            y = self.get_component_data('Y')
            z = self.get_component_data('Z')
            
            h = np.sqrt(x**2 + y**2)
            d = np.degrees(np.arctan2(y, x))
            
            return {
                'H': h.tolist(),
                'D': d.tolist(),
                'Z': z.tolist()
            }
        except ValueError as e:
            raise ValueError(f"Conversion failed: {str(e)}")

    def convert_hdz_to_xyz(self) -> Dict[str, List[float]]:
        """Convert HDZ components to XYZ"""
        try:
            h = self.get_component_data('H')
            d = self.get_component_data('D')
            z = self.get_component_data('Z')
            
            # Convert D to radians
            d_rad = np.radians(d)
            
            x = h * np.cos(d_rad)
            y = h * np.sin(d_rad)
            
            return {
                'X': x.tolist(),
                'Y': y.tolist(),
                'Z': z.tolist()
            }
        except ValueError as e:
            raise ValueError(f"Conversion failed: {str(e)}")

    def get_total_intensity(self, orientation: str = 'auto') -> np.ndarray:
        """Calculate total intensity (F) from either XYZ or HDZ"""
        try:
            if orientation == 'auto':
                orientation = self._detect_orientation()
                
            if orientation == 'XYZ':
                x = self.get_component_data('X')
                y = self.get_component_data('Y')
                z = self.get_component_data('Z')
                return np.sqrt(x**2 + y**2 + z**2)
            
            elif orientation == 'HDZ':
                h = self.get_component_data('H')
                z = self.get_component_data('Z')
                return np.sqrt(h**2 + z**2)
            
        except ValueError as e:
            raise ValueError(f"Total intensity calculation failed: {str(e)}")

    def _detect_orientation(self) -> str:
        """Detect data orientation based on available components"""
        xyz = all(comp in self.data for comp in ['X', 'Y', 'Z'])
        hdz = all(comp in self.data for comp in ['H', 'D', 'Z'])
        
        if xyz and not hdz:
            return 'XYZ'
        elif hdz and not xyz:
            return 'HDZ'
        elif xyz and hdz:
            return self.station_info.get('orientation', 'XYZ').replace('S', '')
        else:
            raise ValueError("Cannot detect orientation - missing components")

    def validate_orientation(self) -> Tuple[bool, str]:
        """Validate orientation consistency"""
        try:
            orientation = self._detect_orientation()
            total_f = self.get_total_intensity(orientation)
            
            if 'F' in self.data or 'S' in self.data:
                recorded_f = self.get_component_data('F' if 'F' in self.data else 'S')
                diff = np.nanmax(np.abs(total_f - recorded_f))
                
                if diff > 1.0:  # 1 nT threshold
                    return False, f"Inconsistent total intensity: max difference {diff:.2f} nT"
                    
            return True, "Orientation consistent"
            
        except ValueError as e:
            return False, str(e)