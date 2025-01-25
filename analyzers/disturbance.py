# analyzers/disturbance.py

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .base_analyzer import BaseAnalyzer
from scipy import signal
from scipy.stats import zscore

class DisturbanceAnalyzer(BaseAnalyzer):
    def __init__(self, data: Dict[str, List], station_code: str):
        super().__init__(data, station_code)
        self.sampling_rate = self._determine_sampling_rate()

    def _determine_sampling_rate(self) -> str:
        """Determine if data is minute or second sampling"""
        times = self.get_datetime_array()
        if len(times) > 1:
            diff = np.diff(times)[0]
            return 'PT1S' if diff == np.timedelta64(1, 's') else 'PT1M'
        return 'PT1M'  # default to minute sampling

    def detect_sudden_commencements(self) -> List[Dict]:
        """Detect Sudden Storm Commencements (SSC) and Sudden Impulses (SI)"""
        h_data = self.get_component_data('H' if 'H' in self.data else 'X')
        times = self.get_datetime_array()
        
        # Calculate gradient
        gradient = np.gradient(h_data)
        
        # Define threshold based on data statistics
        threshold = np.std(gradient) * 3
        
        # Find peaks in absolute gradient
        peaks, properties = signal.find_peaks(np.abs(gradient), 
                                            height=threshold,
                                            distance=self._get_min_peak_distance())
        
        events = []
        for peak, height in zip(peaks, properties['peak_heights']):
            events.append({
                'time': times[peak],
                'magnitude': float(height),
                'type': 'SSC' if height > threshold * 1.5 else 'SI'
            })
            
        return events

    def detect_substorms(self) -> List[Dict]:
        """Detect magnetic substorms using bay-like variations"""
        h_data = self.get_component_data('H' if 'H' in self.data else 'X')
        times = self.get_datetime_array()
        
        # Apply smoothing
        window = self._get_smoothing_window()
        smoothed = np.convolve(h_data, np.ones(window)/window, mode='valid')
        
        # Look for characteristic bay signature
        negative_bays = self._find_bays(smoothed, times[window-1:], negative=True)
        positive_bays = self._find_bays(smoothed, times[window-1:], negative=False)
        
        return negative_bays + positive_bays

    def calculate_k_index(self, window_hours: int = 3) -> List[Dict]:
        """Calculate K-index values"""
        h_data = self.get_component_data('H' if 'H' in self.data else 'X')
        times = self.get_datetime_array()
        
        # Split data into 3-hour windows
        samples_per_window = window_hours * self._get_samples_per_hour()
        windows = np.array_split(h_data, len(h_data)//samples_per_window)
        window_times = np.array_split(times, len(times)//samples_per_window)
        
        k_indices = []
        for window_data, window_time in zip(windows, window_times):
            if len(window_data) == samples_per_window:
                variation = np.max(window_data) - np.min(window_data)
                k_value = self._convert_to_k_value(variation)
                k_indices.append({
                    'start_time': window_time[0],
                    'end_time': window_time[-1],
                    'k_value': k_value,
                    'variation': float(variation)
                })
                
        return k_indices

    def find_disturbed_periods(self) -> List[Dict]:
        """Find periods of sustained magnetic disturbance"""
        components = ['H', 'D', 'Z'] if 'H' in self.data else ['X', 'Y', 'Z']
        times = self.get_datetime_array()
        
        disturbed_periods = []
        for comp in components:
            if comp in self.data:
                data = self.get_component_data(comp)
                z_scores = zscore(data, nan_policy='omit')
                
                # Find periods where |z-score| > 2 for at least 30 minutes
                disturbed = np.abs(z_scores) > 2
                sustained = self._find_sustained_periods(disturbed, times)
                
                for period in sustained:
                    disturbed_periods.append({
                        'component': comp,
                        'start_time': period['start_time'],
                        'end_time': period['end_time'],
                        'max_deviation': float(np.max(np.abs(z_scores[period['start_idx']:period['end_idx']])))
                    })
                    
        return disturbed_periods

    def _get_min_peak_distance(self) -> int:
        """Get minimum distance between peaks based on sampling rate"""
        return 60 if self.sampling_rate == 'PT1S' else 1

    def _get_smoothing_window(self) -> int:
        """Get smoothing window size based on sampling rate"""
        return 300 if self.sampling_rate == 'PT1S' else 5

    def _get_samples_per_hour(self) -> int:
        """Get number of samples per hour based on sampling rate"""
        return 3600 if self.sampling_rate == 'PT1S' else 60

    def _find_bays(self, data: np.ndarray, times: np.ndarray, negative: bool = True) -> List[Dict]:
        """Find bay-like variations in the data"""
        # Implementation of bay detection algorithm
        sign = -1 if negative else 1
        threshold = np.std(data) * 2
        
        bays = []
        i = 0
        while i < len(data) - 1:
            if sign * (data[i+1] - data[i]) < -threshold:
                start_idx = i
                # Look for recovery
                while i < len(data) - 1 and sign * (data[i+1] - data[i]) <= 0:
                    i += 1
                recovery_idx = i
                
                if i - start_idx >= self._get_min_bay_duration():
                    bays.append({
                        'start_time': times[start_idx],
                        'max_time': times[recovery_idx],
                        'magnitude': float(abs(data[recovery_idx] - data[start_idx])),
                        'type': 'negative_bay' if negative else 'positive_bay'
                    })
            i += 1
            
        return bays

    def _find_sustained_periods(self, mask: np.ndarray, times: np.ndarray) -> List[Dict]:
        """Find sustained periods where mask is True"""
        min_duration = 30 * (60 if self.sampling_rate == 'PT1S' else 1)  # 30 minutes
        periods = []
        
        start_idx = None
        for i in range(len(mask)):
            if mask[i] and start_idx is None:
                start_idx = i
            elif not mask[i] and start_idx is not None:
                if i - start_idx >= min_duration:
                    periods.append({
                        'start_time': times[start_idx],
                        'end_time': times[i-1],
                        'start_idx': start_idx,
                        'end_idx': i
                    })
                start_idx = None
                
        return periods

    def _convert_to_k_value(self, variation: float) -> int:
        """Convert variation to K-index value"""
        k_thresholds = [0, 5, 10, 20, 40, 70, 120, 200, 330, 500]
        return np.digitize(variation, k_thresholds)

    def _get_min_bay_duration(self) -> int:
        """Get minimum duration for bay identification"""
        return 900 if self.sampling_rate == 'PT1S' else 15  # 15 minutes