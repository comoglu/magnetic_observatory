# ui/analysis_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit,
    QLabel, QScrollArea, QPushButton, QDialogButtonBox,
    QSplitter, QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl
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
from magnetic_observatory.analyzers.disturbance import DisturbanceAnalyzer
from magnetic_observatory.analyzers.quality import QualityAnalyzer

import os
from scipy import signal
import json
class AnalysisDialog(QDialog):
    """Enhanced dialog for displaying comprehensive data analysis results"""
    
    def __init__(self, data: Dict, station_code: str, parent=None):
        super().__init__(parent)
        self.data = data
        self.station_code = station_code
            # Initialize analyzers
        self.disturbance_analyzer = DisturbanceAnalyzer(data, station_code)
        self.quality_analyzer = QualityAnalyzer(data, station_code)

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
        self.tab_widget.setMinimumWidth(800)
        
        # Add tabs
        self.tab_widget.addTab(self.create_fft_tab(), "FFT Analysis")
        self.tab_widget.addTab(self.create_disturbance_tab(), "Disturbance Analysis")
        self.tab_widget.addTab(self.create_quality_tab(), "Quality Analysis")
        self.tab_widget.addTab(self.create_statistics_tab(), "Statistics")
        self.tab_widget.addTab(self.create_3d_visualization_tab(), "3D Visualization") 
        self.tab_widget.addTab(self.create_polar_plot_tab(), "Polar Plot")
        self.tab_widget.addTab(self.create_spectrogram_tab(), "Spectrogram")

        
        # Details panel (right side)
        details_panel = QWidget()
        details_panel.setMinimumWidth(150)
        details_layout = QVBoxLayout(details_panel)
        
        # Details label
        details_label = QLabel("Detailed Insights")
        details_label.setAlignment(Qt.AlignCenter)
        details_layout.addWidget(details_label)
        
        # Details text widget
        self.detail_text = QTextEdit()  # Explicitly initialize self.detail_text
        self.detail_text.setReadOnly(True)
        details_layout.addWidget(self.detail_text)

        # Add tab change handler
        self.tab_widget.currentChanged.connect(
            lambda index: self.update_details(self.tab_widget.tabText(index))
        )

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

    def update_details(self, tab_name: str):
        """Update details panel based on selected tab"""
        if tab_name == "FFT Analysis":
            self._show_fft_insights()
        elif tab_name == "Disturbance Analysis":
            self._show_disturbance_insights()
        elif tab_name == "Quality Analysis":
            self._show_quality_insights()
        elif tab_name == "3D Visualization" or tab_name == "Polar Plot":
            self._show_component_insights()
        elif tab_name == "Spectrogram":
            self._show_frequency_insights()
        elif tab_name == "Statistics":
            self._show_statistics_insights()
        elif tab_name == "Polar Plot":
            self._show_polar_insights()

    def _show_component_insights(self):
        components = ['H', 'D', 'Z']
        insights = []
        
        for comp in components:
            if comp in self.data:
                values = np.array([x for x in self.data[comp] if x is not None])
                insights.append(f"{comp} Component:")
                insights.append(f"Mean: {np.mean(values):.2f} nT")
                insights.append(f"Std Dev: {np.std(values):.2f} nT")
                insights.append(f"Range: {np.ptp(values):.2f} nT\n")
        
        self.detail_text.setText("\n".join(insights))

    def _show_fft_insights(self):
        insights = []
        components = ['H', 'D', 'Z']
        
        for comp in components:
            if comp in self.data:
                values = np.array([x for x in self.data[comp] if x is not None])
                fft = np.fft.fft(values)
                freqs = np.fft.fftfreq(len(values))
                
                # Find dominant frequencies
                power = np.abs(fft)
                top_idx = np.argsort(power)[-3:][::-1]
                
                insights.append(f"{comp} Component Frequencies:")
                for i, idx in enumerate(top_idx, 1):
                    insights.append(f"Peak {i}: {abs(freqs[idx]):.4f} Hz (Power: {power[idx]:.1f})")
                insights.append("")
                
        self.detail_text.setText("\n".join(insights))

    def _show_disturbance_insights(self):
        insights = []
        
        # K-index summary
        k_indices = self.disturbance_analyzer.calculate_k_index()
        if k_indices:
            max_k = max(k['k_value'] for k in k_indices)
            min_k = min(k['k_value'] for k in k_indices)
            insights.append(f"K-index range: {min_k}-{max_k}")
            
        # Sudden commencements
        ssc = self.disturbance_analyzer.detect_sudden_commencements()
        insights.append(f"\nDetected events: {len(ssc)}")
        if ssc:
            insights.append("Most significant SSC:")
            max_ssc = max(ssc, key=lambda x: x['magnitude'])
            insights.append(f"Time: {max_ssc['time']}")
            insights.append(f"Magnitude: {max_ssc['magnitude']:.1f} nT")
        
        self.detail_text.setText("\n".join(insights))

    def _show_quality_insights(self):
        insights = []
        
        # Data gaps
        gaps = self.quality_analyzer.analyze_data_gaps()
        if gaps:
            total_gap_time = sum((g['end_time'] - g['start_time']).total_seconds() for g in gaps)
            insights.append(f"Data gaps: {len(gaps)}")
            insights.append(f"Total gap time: {total_gap_time/60:.1f} minutes")
        
        # Quality metrics
        metrics = self.quality_analyzer.get_quality_metrics()
        for comp, metric in metrics.items():
            insights.append(f"\n{comp} Quality:")
            insights.append(f"Completeness: {metric['completeness']:.1%}")
            insights.append(f"Noise level: {metric['noise_level']:.2f}")
        
        self.detail_text.setText("\n".join(insights))

    def _show_frequency_insights(self):
        insights = []
        components = ['H', 'D', 'Z']
        
        for comp in components:
            if comp in self.data:
                values = np.array([x for x in self.data[comp] if x is not None])
                f, t, Sxx = signal.spectrogram(values, fs=1.0, nperseg=256)
                
                max_power_freq = f[np.argmax(np.mean(Sxx, axis=1))]
                insights.append(f"{comp} Component:")
                insights.append(f"Dominant frequency: {max_power_freq:.4f} Hz")
                insights.append(f"Max power: {np.max(Sxx):.1f}\n")
        
        self.detail_text.setText("\n".join(insights))

    def _show_statistics_insights(self):
        insights = []
        components = ['H', 'D', 'Z']
        
        for comp in components:
            if comp in self.data:
                values = np.array([x for x in self.data[comp] if x is not None])
                insights.extend([
                    f"{comp} Statistics:",
                    f"Skewness: {stats.skew(values):.2f}",
                    f"Kurtosis: {stats.kurtosis(values):.2f}",
                    f"Q1: {np.percentile(values, 25):.2f}",
                    f"Q3: {np.percentile(values, 75):.2f}\n"
                ])
        
        self.detail_text.setText("\n".join(insights))

    def _show_polar_insights(self):
        insights = []
        
        if 'H' in self.data and 'D' in self.data:
            h = np.array([x for x in self.data['H'] if x is not None])
            d = np.array([x for x in self.data['D'] if x is not None])
            
            magnitude = np.sqrt(h**2 + d**2)
            angle = np.arctan2(d, h) * 180 / np.pi
            
            insights.extend([
                "Field Vector Analysis:",
                f"Mean magnitude: {np.mean(magnitude):.2f} nT",
                f"Max magnitude: {np.max(magnitude):.2f} nT",
                f"Mean angle: {np.mean(angle):.2f}°",
                f"Angular range: {np.ptp(angle):.2f}°"
            ])
        
        self.detail_text.setText("\n".join(insights))

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

    # Add this method to the AnalysisDialog class
    def create_3d_visualization_tab(self) -> QWidget:
        """Create 3D visualization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        browser = QWebEngineView()
        browser.setMinimumHeight(600)
        layout.addWidget(browser)
        
        try:
            # Create CSV data as a string
            csv_data = ['datetime,H,D,Z']
            for i, dt in enumerate(self.data['datetime']):
                h = self.data.get('H', [None])[i] if 'H' in self.data else self.data.get('X', [None])[i]
                d = self.data.get('D', [None])[i] if 'D' in self.data else self.data.get('Y', [None])[i]
                z = self.data.get('Z', [None])[i]
                if all(v is not None for v in [h, d, z]):
                    csv_data.append(f"{dt},{h},{d},{z}")
            
            csv_string = '\n'.join(csv_data)
            
            # Create 3D visualization HTML with embedded data
            html_content = '''<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/react/17.0.2/umd/react.production.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/17.0.2/umd/react-dom.production.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prop-types/15.7.2/prop-types.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/recharts/2.1.12/Recharts.min.js"></script>
        <style>
            body { margin: 0; padding: 20px; }
            #root { width: 100%; height: 100vh; }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script>
            const { useState, useEffect } = React;
            const { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, Legend } = Recharts;

            function Magnetic3DViewer() {
                const [data, setData] = useState([]);
                const [angle, setAngle] = useState(0);

                useEffect(() => {
                    const csvData = `''' + csv_string + '''`;
                    const lines = csvData.split('\\n');
                    const processed = lines.slice(1)
                        .filter(line => line.trim())
                        .map(line => {
                            const [datetime, h, d, z] = line.split(',');
                            return {
                                x: parseFloat(h || 0),
                                y: parseFloat(d || 0),
                                z: parseFloat(z || 0),
                                timestamp: datetime
                            };
                        })
                        .filter(point => !isNaN(point.x) && !isNaN(point.y) && !isNaN(point.z));
                    setData(processed);
                }, []);

                const transformedData = data.map(point => ({
                    ...point,
                    x: point.x * Math.cos(angle * Math.PI / 180) - point.y * Math.sin(angle * Math.PI / 180),
                    y: point.x * Math.sin(angle * Math.PI / 180) + point.y * Math.cos(angle * Math.PI / 180)
                }));

                return React.createElement('div', { style: { display: 'flex', flexDirection: 'column', alignItems: 'center' } },
                    React.createElement('h2', null, '3D Magnetic Field Components'),
                    React.createElement(ScatterChart, {
                        width: 800,
                        height: 400,
                        margin: { top: 20, right: 20, bottom: 20, left: 20 }
                    },
                        React.createElement(CartesianGrid),
                        React.createElement(XAxis, { type: 'number', dataKey: 'x', name: 'H/X', unit: 'nT' }),
                        React.createElement(YAxis, { type: 'number', dataKey: 'y', name: 'D/Y', unit: 'nT' }),
                        React.createElement(ZAxis, { type: 'number', dataKey: 'z', name: 'Z', unit: 'nT', range: [60, 600] }),
                        React.createElement(Tooltip, { 
                            cursor: { strokeDasharray: '3 3' },
                            formatter: (value) => [`${value.toFixed(2)} nT`]
                        }),
                        React.createElement(Legend),
                        React.createElement(Scatter, {
                            name: 'Magnetic Field Vector',
                            data: transformedData,
                            fill: '#8884d8'
                        })
                    ),
                    React.createElement('div', { style: { marginTop: '20px' } },
                        React.createElement('input', {
                            type: 'range',
                            min: 0,
                            max: 360,
                            value: angle,
                            onChange: (e) => setAngle(parseInt(e.target.value)),
                            style: { width: '300px' }
                        }),
                        React.createElement('span', { style: { marginLeft: '10px' } },
                            `Rotation: ${angle}°`
                        )
                    )
                );
            }

            ReactDOM.render(
                React.createElement(Magnetic3DViewer),
                document.getElementById('root')
            );
        </script>
    </body>
    </html>'''
            
            browser.setHtml(html_content)

        except Exception as e:
            error_text = QTextEdit()
            error_text.setPlainText(f"Error creating 3D visualization: {str(e)}")
            layout.addWidget(error_text)
        
        return tab

    def create_polar_plot_tab(self) -> QWidget:
        """Create polar plot visualization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        browser = QWebEngineView()
        browser.setMinimumHeight(600)
        layout.addWidget(browser)
        
        try:
            # Prepare data
            h_data = self.data.get('H', self.data.get('X', []))
            d_data = self.data.get('D', self.data.get('Y', []))
            times = self.data['datetime']
            
            # Create data string
            data_points = []
            for i, (h, d, t) in enumerate(zip(h_data, d_data, times)):
                if h is not None and d is not None:
                    data_points.append(f"{{'h': {h}, 'd': {d}, 'time': '{t}'}}")
            
            data_string = f"[{','.join(data_points)}]"
            
            html_content = '''<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.24.2/plotly.min.js"></script>
        <style>
            body { margin: 0; padding: 20px; }
            #plot { width: 100%; height: 600px; }
        </style>
    </head>
    <body>
        <div id="plot"></div>
        <script>
            const data = ''' + data_string + ''';
            
            const trace = {
                type: 'scatterpolar',
                r: data.map(d => Math.sqrt(d.h * d.h + d.d * d.d)),
                theta: data.map(d => Math.atan2(d.d, d.h) * 180 / Math.PI),
                mode: 'markers+lines',
                marker: {
                    color: Array.from({length: data.length}, (_, i) => i),
                    colorscale: 'Viridis',
                    size: 8,
                    showscale: true,
                    colorbar: {
                        title: 'Time Progression'
                    }
                },
                hovertemplate: 
                    'H: %{customdata[0]:.2f} nT<br>' +
                    'D: %{customdata[1]:.2f} nT<br>' +
                    'Time: %{customdata[2]}<br>' +
                    '<extra></extra>',
                customdata: data.map(d => [d.h, d.d, d.time])
            };

            const layout = {
                polar: {
                    radialaxis: {
                        title: 'Field Intensity (nT)',
                        showgrid: true,
                    },
                    angularaxis: {
                        tickmode: 'array',
                        ticktext: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                        tickvals: [0, 45, 90, 135, 180, 225, 270, 315],
                    }
                },
                title: 'Magnetic Field Polar Plot',
                showlegend: false,
                width: 800,
                height: 600
            };

            Plotly.newPlot('plot', [trace], layout);
        </script>
    </body>
    </html>'''
            
            browser.setHtml(html_content)

        except Exception as e:
            error_text = QTextEdit()
            error_text.setPlainText(f"Error creating polar plot: {str(e)}")
            layout.addWidget(error_text)
        
        return tab

    def create_spectrogram_tab(self) -> QWidget:
        """Create spectrogram visualization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        browser = QWebEngineView()
        browser.setMinimumHeight(600)
        layout.addWidget(browser)
        
        try:
            # Prepare data for all components
            components = {'H': self.data.get('H', self.data.get('X', [])),
                            'D': self.data.get('D', self.data.get('Y', [])),
                            'Z': self.data.get('Z', [])}
            
            # Calculate spectrograms
            spectrograms = {}
            for comp_name, comp_data in components.items():
                if comp_data:
                    # Convert to numpy array and handle NaN
                    data = np.array([x if x is not None else 0 for x in comp_data])
                    
                    # Calculate spectrogram using scipy
                    f, t, Sxx = signal.spectrogram(data, fs=1.0, nperseg=256, noverlap=128)
                    
                    # Convert to list for JSON
                    spectrograms[comp_name] = {
                        'frequencies': f.tolist(),
                        'times': t.tolist(),
                        'power': Sxx.tolist()
                    }
            
            html_content = '''<!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.24.2/plotly.min.js"></script>
        <style>
            body { margin: 0; padding: 20px; }
            .plot { width: 100%; height: 300px; margin-bottom: 20px; }
        </style>
        </head>
        <body>
        <div id="plot-H" class="plot"></div>
        <div id="plot-D" class="plot"></div>
        <div id="plot-Z" class="plot"></div>
        <script>
            const spectrograms = ''' + json.dumps(spectrograms) + ''';
            
            for (const [comp, data] of Object.entries(spectrograms)) {
                const trace = {
                    z: data.power,
                    x: data.times,
                    y: data.frequencies,
                    type: 'heatmap',
                    colorscale: 'Viridis',
                    colorbar: {
                        title: 'Power'
                    }
                };

                const layout = {
                    title: `${comp} Component Spectrogram`,
                    xaxis: {title: 'Time (samples)'},
                    yaxis: {title: 'Frequency (Hz)'},
                    height: 300
                };

                Plotly.newPlot(`plot-${comp}`, [trace], layout);
            }
        </script>
        </body>
        </html>'''
            
            browser.setHtml(html_content)

        except Exception as e:
            error_text = QTextEdit()
            error_text.setPlainText(f"Error creating spectrogram: {str(e)}")
            layout.addWidget(error_text)
        
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
