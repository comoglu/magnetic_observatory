# analyzers/quality.py

import numpy as np
from typing import Dict, List, Tuple
from .base_analyzer import BaseAnalyzer
from ..utils.constants import QC_PARAMS

class QualityAnalyzer(BaseAnalyzer):
    def analyze_data_gaps(self) -> List[Dict]:
        """Analyze temporal gaps in data"""
        times = self.get_datetime_array()
        time_diffs = np.diff(times)
        gaps = np.where(time_diffs > np.timedelta64(QC_PARAMS['max_gap_minutes'], 'm'))[0]
        
        return [
            {
                'start_time': times[gap],
                'end_time': times[gap + 1],
                'duration': time_diffs[gap]
            }
            for gap in gaps
        ]

    def detect_spikes(self, component: str) -> List[Dict]:
        """Detect unusual spikes in component data"""
        data = self.get_component_data(component)
        rolling_mean = self._calculate_rolling_mean(data)
        rolling_std = self._calculate_rolling_std(data)
        
        threshold = QC_PARAMS['spike_threshold'] * rolling_std
        spikes = np.where(np.abs(data - rolling_mean) > threshold)[0]
        
        return [
            {
                'time': self.data['datetime'][idx],
                'value': float(data[idx]),
                'deviation': float(abs(data[idx] - rolling_mean[idx]))
            }
            for idx in spikes
        ]

    def check_baseline_stability(self) -> Dict[str, List[Dict]]:
        """Check baseline stability for all components"""
        results = {}
        for component in self.get_available_components():
            data = self.get_component_data(component)
            jumps = self._detect_baseline_jumps(data)
            if jumps:
                results[component] = jumps
        return results

    def get_quality_metrics(self) -> Dict[str, Dict]:
        """Calculate quality metrics for available components"""
        metrics = {}
        # Use get_available_components to only process existing ones
        for component in self.get_available_components():
            try:
                data = self.get_component_data(component)
                metrics[component] = {
                    'completeness': self._calculate_completeness(data),
                    'noise_level': self._calculate_noise_level(data),
                    'stability': self._calculate_stability(data)
                }
            except ValueError:
                continue  # Skip components with invalid data
        return metrics

    def _calculate_rolling_mean(self, data: np.ndarray, window: int = 60) -> np.ndarray:
        """Calculate rolling mean with handling of NaN values"""
        return np.convolve(np.nan_to_num(data), 
                          np.ones(window)/window, 
                          mode='same')

    def _calculate_rolling_std(self, data: np.ndarray, window: int = 60) -> np.ndarray:
        """Calculate rolling standard deviation"""
        return np.array([np.nanstd(data[max(0, i-window//2):min(len(data), i+window//2)]) 
                        for i in range(len(data))])

    def _detect_baseline_jumps(self, data: np.ndarray) -> List[Dict]:
        """Detect sudden jumps in baseline"""
        diff = np.diff(data)
        threshold = QC_PARAMS['baseline_jump_threshold'] * np.nanstd(diff)
        jumps = np.where(np.abs(diff) > threshold)[0]
        
        return [
            {
                'time': self.data['datetime'][idx],
                'magnitude': float(diff[idx])
            }
            for idx in jumps
        ]

    def _calculate_completeness(self, data: np.ndarray) -> float:
        """Calculate data completeness ratio"""
        return 1 - np.sum(np.isnan(data)) / len(data)

    def _calculate_noise_level(self, data: np.ndarray) -> float:
        """Calculate noise level using median absolute deviation"""
        return float(np.nanmedian(np.abs(np.diff(data))))

    def _calculate_stability(self, data: np.ndarray) -> float:
        """Calculate baseline stability metric"""
        return float(np.nanstd(data))