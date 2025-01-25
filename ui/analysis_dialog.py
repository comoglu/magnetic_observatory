# ui/analysis_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit,
    QLabel, QScrollArea, QPushButton, QDialogButtonBox,
    QSplitter, QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import scipy.stats as stats
from typing import Dict, List, Optional
from magnetic_observatory.utils.data_handlers import DataProcessor
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from magnetic_observatory.analyzers.disturbance import DisturbanceAnalyzer
from magnetic_observatory.analyzers.quality import QualityAnalyzer
from magnetic_observatory.analyzers.orientation import OrientationAnalyzer

class AnalysisDialog(QDialog):
    """Enhanced dialog for displaying comprehensive data analysis results"""
    
    def __init__(self, data: Dict, station_code: str, parent=None):
        super().__init__(parent)
        self.data = data
        self.station_code = station_code
        
        # Initialize UI first
        self.init_ui()
        
    def init_ui(self):
        """Initialize the enhanced user interface"""
        self.setWindowTitle(f"Magnetic Data Analysis - {self.station_code}")
        self.setMinimumSize(1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create main horizontal layout
        main_horizontal_layout = QHBoxLayout()
        
        # Tab widget (left side)
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumWidth(600)
        
        # Add tabs
        self.tab_widget.addTab(self.create_fft_tab(), "FFT Analysis")
        self.tab_widget.addTab(self.create_disturbance_tab(), "Disturbance Analysis")
        self.tab_widget.addTab(self.create_quality_tab(), "Quality Analysis")
        self.tab_widget.addTab(self.create_statistics_tab(), "Statistics")
        
        # Details panel (right side)
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        
        # Details label
        details_label = QLabel("Detailed Insights")
        details_label.setAlignment(Qt.AlignCenter)
        details_layout.addWidget(details_label)
        
        # Details text widget
        self.detail_text = QTextEdit()  # Explicitly initialize self.detail_text
        self.detail_text.setReadOnly(True)
        details_layout.addWidget(self.detail_text)
        
        # Add widgets to main horizontal layout
        main_horizontal_layout.addWidget(self.tab_widget)
        main_horizontal_layout.addWidget(details_panel)
        
        # Add horizontal layout to main layout
        main_layout.addLayout(main_horizontal_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Close,
            Qt.Horizontal,
            self
        )
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def create_fft_tab(self) -> QWidget:
        """Create FFT analysis tab with enhanced analysis"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add FFT plot 
        browser = QWebEngineView()
        browser.setMinimumHeight(600)  # Increased height
        layout.addWidget(browser)
        
        # Create a text area for insights
        insights_text = QTextEdit()
        insights_text.setReadOnly(True)
        layout.addWidget(insights_text)
        
        # Prepare FFT analysis
        fft_insights = []
        
        try:
            # Create subplot for FFT analysis
            fig = make_subplots(
                rows=4, cols=1,
                subplot_titles=['FFT of H', 'FFT of D', 'FFT of Z', 'Frequency Analysis'],
                vertical_spacing=0.1,
            )
            
            # Components to analyze
            components = ['H', 'D', 'Z', 'F']
            
            for i, comp in enumerate(components, 1):
                if comp in self.data:
                    # Remove None values and convert to numpy array
                    values = np.array([x if x is not None else 0 for x in self.data[comp]])
                    
                    # Perform FFT
                    fft_vals = np.fft.fft(values)
                    freqs = np.fft.fftfreq(len(values))
                    
                    # Positive frequencies
                    pos_freq_mask = freqs > 0
                    pos_freqs = freqs[pos_freq_mask]
                    pos_fft_vals = np.abs(fft_vals[pos_freq_mask])
                    
                    # Add trace
                    fig.add_trace(
                        go.Scatter(x=pos_freqs, y=pos_fft_vals, name=comp),
                        row=i, col=1
                    )
                    
                    # Analyze dominant frequencies
                    dominant_idx = np.argsort(pos_fft_vals)[-3:][::-1]
                    top_freqs = pos_freqs[dominant_idx]
                    top_powers = pos_fft_vals[dominant_idx]
                    
                    fft_insights.append(f"{comp} Component Frequency Analysis:")
                    for j, (freq, power) in enumerate(zip(top_freqs, top_powers), 1):
                        fft_insights.append(f"  Top Frequency {j}: {freq:.4f} Hz (Power: {power:.2f})")
            
            fig.update_layout(showlegend=True, height=800)
            browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
            
            # Update insights text
            insights_text.setPlainText("\n".join(fft_insights))
            
        except Exception as e:
            error_msg = f"FFT Analysis Error: {str(e)}"
            print(error_msg)
            insights_text.setPlainText(error_msg)
        
        return tab

    def create_disturbance_tab(self) -> QWidget:
        """Create disturbance analysis tab with comprehensive insights"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create text area for insights
        insights_text = QTextEdit()
        insights_text.setReadOnly(True)
        layout.addWidget(insights_text)
        
        # Web view for potential visualizations
        browser = QWebEngineView()
        browser.setMinimumHeight(300)
        layout.addWidget(browser)
        
        try:
            # Create disturbance analyzer
            disturbance_analyzer = DisturbanceAnalyzer(self.data, self.station_code)
            
            # Perform various disturbance analyses
            insights = []
            
            # 1. Sudden Commencements
            ssc_events = disturbance_analyzer.detect_sudden_commencements()
            insights.append("Sudden Storm Commencements (SSC):")
            if ssc_events:
                for event in ssc_events[:5]:  # Limit to 5 events
                    event_time = np.datetime_as_string(event['time'], unit='s')
                    insights.append(f"  - Time: {event_time}, Type: {event['type']}, Magnitude: {event['magnitude']:.2f}")
            else:
                insights.append("  No sudden commencements detected")
            
            # 2. Substorms
            substorms = disturbance_analyzer.detect_substorms()
            insights.append("\nSubstorm Events:")
            if substorms:
                for storm in substorms[:5]:  # Limit to 5 events
                    storm_time = np.datetime_as_string(storm['start_time'], unit='s')
                    insights.append(f"  - Time: {storm_time}, Type: {storm['type']}, Magnitude: {storm['magnitude']:.2f}")
            else:
                insights.append("  No substorms detected")
            
            # 3. K-index Calculation
            k_indices = disturbance_analyzer.calculate_k_index()
            insights.append("\nGeomagnetic Activity (K-index):")
            if k_indices:
                for index in k_indices:
                    start_time = np.datetime_as_string(index['start_time'], unit='s')
                    end_time = np.datetime_as_string(index['end_time'], unit='s')
                    insights.append(f"  - Period: {start_time} to {end_time}, K-value: {index['k_value']}")
            else:
                insights.append("  No K-index data available")
            
            # 4. Disturbed Periods
            disturbed_periods = disturbance_analyzer.find_disturbed_periods()
            insights.append("\nMagnetic Disturbance Periods:")
            if disturbed_periods:
                for period in disturbed_periods[:5]:  # Limit to 5 periods
                    start_time = np.datetime_as_string(period['start_time'], unit='s')
                    end_time = np.datetime_as_string(period['end_time'], unit='s')
                    insights.append(f"  - Component: {period['component']}")
                    insights.append(f"    Start: {start_time}")
                    insights.append(f"    End: {end_time}")
                    insights.append(f"    Max Deviation: {period['max_deviation']:.2f}")
            else:
                insights.append("  No significant disturbed periods detected")
            
            # Update text area
            insights_text.setPlainText("\n".join(insights))
            
            # Optional: Create a simple visualization of disturbances
            if ssc_events or substorms:
                fig = go.Figure()
                
                # Plot SSC events
                if ssc_events:
                    ssc_times = [event['time'] for event in ssc_events]
                    ssc_magnitudes = [event['magnitude'] for event in ssc_events]
                    fig.add_trace(go.Scatter(
                        x=ssc_times, 
                        y=ssc_magnitudes, 
                        mode='markers', 
                        name='Sudden Commencements',
                        marker=dict(color='red', size=10)
                    ))
                
                # Plot Substorm events
                if substorms:
                    substorm_times = [storm['start_time'] for storm in substorms]
                    substorm_magnitudes = [storm['magnitude'] for storm in substorms]
                    fig.add_trace(go.Scatter(
                        x=substorm_times, 
                        y=substorm_magnitudes, 
                        mode='markers', 
                        name='Substorms',
                        marker=dict(color='blue', size=8)
                    ))
                
                fig.update_layout(
                    title='Magnetic Disturbance Events',
                    xaxis_title='Time',
                    yaxis_title='Magnitude'
                )
                browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
        
        except Exception as e:
            error_msg = f"Disturbance Analysis Error: {str(e)}"
            insights_text.setPlainText(error_msg)
        
        return tab

    def create_quality_tab(self) -> QWidget:
        """Create data quality analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Insights text area
        insights_text = QTextEdit()
        insights_text.setReadOnly(True)
        layout.addWidget(insights_text)
        
        # Visualization browser
        browser = QWebEngineView()
        browser.setMinimumHeight(300)
        layout.addWidget(browser)
        
        try:
            # Create quality analyzer
            quality_analyzer = QualityAnalyzer(self.data, self.station_code)
            available_components = quality_analyzer.get_available_components()
            insights = []
            
            # 1. Data Gaps
            data_gaps = quality_analyzer.analyze_data_gaps()
            insights.append("Data Gaps:")
            if data_gaps:
                for gap in data_gaps:
                    insights.append(f"  - From {gap['start_time']} to {gap['end_time']}, Duration: {gap['duration']}")
            else:
                insights.append("  No significant data gaps detected")
            
            # 2. Spikes Detection
            spike_insights = {}
            for component in available_components:
                try:
                    spikes = quality_analyzer.detect_spikes(component)
                    if spikes:
                        spike_insights[component] = spikes
                except ValueError:
                    continue
            
            insights.append("\nSpike Detection:")
            if spike_insights:
                for comp, spikes in spike_insights.items():
                    insights.append(f"  {comp} Component Spikes:")
                    for spike in spikes[:5]:  # Limit to 5 spikes per component
                        insights.append(f"    - Time: {spike['time']}, Value: {spike['value']:.2f}, Deviation: {spike['deviation']:.2f}")
            else:
                insights.append("  No significant spikes detected")
            
            # 3. Baseline Stability
            baseline_stability = quality_analyzer.check_baseline_stability()
            insights.append("\nBaseline Jumps:")
            if baseline_stability:
                for comp, jumps in baseline_stability.items():
                    insights.append(f"  {comp} Component:")
                    for jump in jumps[:5]:  # Limit to 5 jumps per component
                        insights.append(f"    - Time: {jump['time']}, Magnitude: {jump['magnitude']:.2f}")
            else:
                insights.append("  No significant baseline jumps detected")
            
            # 4. Quality Metrics
            quality_metrics = {}
            for comp in available_components:
                try:
                    metrics = quality_analyzer.get_quality_metrics()
                    if comp in metrics:
                        quality_metrics[comp] = metrics[comp]
                except ValueError:
                    continue
                    
            insights.append("\nQuality Metrics:")
            for comp, metrics in quality_metrics.items():
                insights.append(f"  {comp} Component:")
                insights.append(f"    Completeness: {metrics['completeness']:.2%}")
                insights.append(f"    Noise Level: {metrics['noise_level']:.4f}")
                insights.append(f"    Stability: {metrics['stability']:.4f}")
            
            # Update text area
            insights_text.setPlainText("\n".join(insights))
            
            # Visualization of data quality metrics
            if quality_metrics:
                fig = go.Figure()
                
                # Prepare data for visualization
                components = list(quality_metrics.keys())
                completeness = [metrics['completeness'] for metrics in quality_metrics.values()]
                noise_levels = [metrics['noise_level'] for metrics in quality_metrics.values()]
                stability = [metrics['stability'] for metrics in quality_metrics.values()]
                
                # Add traces for each metric
                fig.add_trace(go.Bar(x=components, y=completeness, name='Completeness'))
                fig.add_trace(go.Bar(x=components, y=noise_levels, name='Noise Level'))
                fig.add_trace(go.Bar(x=components, y=stability, name='Stability'))
                
                fig.update_layout(
                    title='Data Quality Metrics',
                    barmode='group',
                    xaxis_title='Components',
                    yaxis_title='Metrics',
                    height=500
                )
                
                browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
            else:
                browser.setHtml("<h3>No quality metrics available for visualization</h3>")
        
        except Exception as e:
            error_msg = f"Quality Analysis Note: {str(e)}"
            insights_text.setPlainText(error_msg)
        
        return tab

    def create_statistics_tab(self) -> QWidget:
        """Create statistical analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Insights text area
        insights_text = QTextEdit()
        insights_text.setReadOnly(True)
        layout.addWidget(insights_text)
        
        # Visualization browser
        browser = QWebEngineView()
        browser.setMinimumHeight(300)
        layout.addWidget(browser)
        
        try:
            # Orientation analysis
            orientation_analyzer = OrientationAnalyzer(self.data, self.station_code)
            
            insights = []
            
            # Detect orientation
            try:
                orientation = orientation_analyzer._detect_orientation()
                insights.append(f"Data Orientation: {orientation}")
            except ValueError as e:
                insights.append(f"Orientation Detection Error: {str(e)}")
            
            # Validate orientation
            try:
                is_valid, message = orientation_analyzer.validate_orientation()
                insights.append(f"\nOrientation Validation: {'Valid' if is_valid else 'Invalid'}")
                insights.append(f"Details: {message}")
            except Exception as e:
                insights.append(f"Orientation Validation Error: {str(e)}")
            
            # Total intensity calculation
            try:
                total_intensity = orientation_analyzer.get_total_intensity()
                insights.append("\nTotal Intensity (F):")
                insights.append(f"  Mean: {np.nanmean(total_intensity):.2f}")
                insights.append(f"  Median: {np.nanmedian(total_intensity):.2f}")
                insights.append(f"  Standard Deviation: {np.nanstd(total_intensity):.2f}")
                insights.append(f"  Min: {np.nanmin(total_intensity):.2f}")
                insights.append(f"  Max: {np.nanmax(total_intensity):.2f}")
            except Exception as e:
                insights.append(f"Total Intensity Calculation Error: {str(e)}")
            
            # Coordinate conversions
            try:
                if orientation == 'XYZ':
                    hdz_data = orientation_analyzer.convert_xyz_to_hdz()
                    insights.append("\nXYZ to HDZ Conversion:")
                    for comp, stats in hdz_data.items():
                        insights.append(f"  {comp} Component:")
                        insights.append(f"    Mean: {np.nanmean(stats):.2f}")
                        insights.append(f"    Median: {np.nanmedian(stats):.2f}")
                        insights.append(f"    Standard Deviation: {np.nanstd(stats):.2f}")
                elif orientation == 'HDZ':
                    xyz_data = orientation_analyzer.convert_hdz_to_xyz()
                    insights.append("\nHDZ to XYZ Conversion:")
                    for comp, stats in xyz_data.items():
                        insights.append(f"  {comp} Component:")
                        insights.append(f"    Mean: {np.nanmean(stats):.2f}")
                        insights.append(f"    Median: {np.nanmedian(stats):.2f}")
                        insights.append(f"    Standard Deviation: {np.nanstd(stats):.2f}")
            except Exception as e:
                insights.append(f"Coordinate Conversion Error: {str(e)}")
            
            # Update text area
            insights_text.setPlainText("\n".join(insights))
            
            # Visualization of total intensity
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=total_intensity, name='Total Intensity'))
            fig.update_layout(
                title='Total Magnetic Intensity Distribution',
                xaxis_title='Total Intensity (nT)',
                yaxis_title='Frequency'
            )
            
            browser.setHtml(fig.to_html(include_plotlyjs='cdn'))
        
        except Exception as e:
            error_msg = f"Statistics Analysis Error: {str(e)}"
            insights_text.setPlainText(error_msg)
        
        return tab
