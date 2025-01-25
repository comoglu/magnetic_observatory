# ui/components.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QCalendarWidget, QSpinBox, QPushButton,
                           QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
from typing import Dict, List, Optional

class ControlPanel(QWidget):
    """Left panel with control widgets"""
    
    def __init__(self, station_info: Dict):
        super().__init__()
        self.station_info = station_info
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Station selection
        layout.addWidget(QLabel("Station:"))
        self.station_select = QComboBox()
        self.station_select.addItems([
            f"{code} ({info['name']})" 
            for code, info in self.station_info.items()
        ])
        layout.addWidget(self.station_select)
        
        # Station info display
        self.station_info_display = QTextEdit()
        self.station_info_display.setReadOnly(True)
        self.station_info_display.setMaximumHeight(100)
        layout.addWidget(self.station_info_display)
        
        # Calendar
        layout.addWidget(QLabel("Date Selection:"))
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMaximumWidth(300)
        layout.addWidget(self.calendar)
        
        # Duration selector
        dur_layout = QHBoxLayout()
        self.duration = QSpinBox()
        self.duration.setRange(1, 366)
        self.duration.setValue(1)
        dur_layout.addWidget(QLabel("Duration (days):"))
        dur_layout.addWidget(self.duration)
        layout.addLayout(dur_layout)
        
        # Data options
        self.sample_rate = QComboBox()
        self.sample_rate.addItems(["Minute", "Second"])
        layout.addWidget(QLabel("Sample Rate:"))
        layout.addWidget(self.sample_rate)
        
        self.pub_state = QComboBox()
        self.pub_state.addItems([
            "reported", "adjusted", "quasi-def", 
            "definitive", "best-avail"
        ])
        layout.addWidget(QLabel("Publication State:"))
        layout.addWidget(self.pub_state)
        
        self.orientation = QComboBox()
        self.orientation.addItems([
            "Native", "XYZF", "HDZF", "DIFF", 
            "XYZS", "HDZS", "DIFS"
        ])
        layout.addWidget(QLabel("Orientation:"))
        layout.addWidget(self.orientation)
        
        # Fetch button
        self.fetch_btn = QPushButton("Fetch Data")
        layout.addWidget(self.fetch_btn)

        layout.addStretch()
        self.station_select.currentTextChanged.emit(self.station_select.currentText())        

class DataTable(QTableWidget):
    """Table display for magnetic data"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            'Time', 'H (nT)', 'D (min)', 
            'Z (nT)', 'F (nT)'
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
    def update_data(self, data: Dict):
        self.setRowCount(0)
        if not data or 'datetime' not in data:
            return
            
        for i, timestamp in enumerate(data['datetime']):
            self.insertRow(i)
            self.setItem(i, 0, QTableWidgetItem(timestamp))
            
            components = ['H', 'D', 'Z', 'S']
            for j, comp in enumerate(components, 1):
                if comp in data and i < len(data[comp]):
                    value = data[comp][i]
                    if value is not None:
                        if comp == 'D':
                            value *= 60  # Convert to minutes
                        self.setItem(i, j, QTableWidgetItem(f"{value:.2f}"))

class PlotPanel(QWidget):
    """Panel for displaying interactive plots"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.browser = QWebEngineView()
        self.browser.setMinimumHeight(400)
        layout.addWidget(self.browser)
        
    def update_plot(self, data: Dict, station_name: str):
        if not data or 'datetime' not in data:
            return
            
        # Create subplots for each component
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=self._generate_subplot_titles(data),
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.25, 0.25, 0.25, 0.25]
        )
        
        # Add traces for each component
        components = ['H', 'D', 'Z', 'S']
        colors = ['red', 'green', 'blue', 'black']
        
        for i, (comp, color) in enumerate(zip(components, colors), 1):
            if comp in data:
                self._add_component_trace(fig, data, comp, color, i)
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=False,
            title=dict(
                text=f"Magnetic Observatory Data - {station_name}",
                x=0.5,
                y=0.95
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='rgb(200, 200, 200)', gridwidth=0.5),
            yaxis=dict(showgrid=True, gridcolor='rgb(200, 200, 200)', gridwidth=0.5)
        )

        # Add grid for each subplot
        for i in range(1, 5):
            fig.update_xaxes(showgrid=True, gridcolor='rgb(200, 200, 200)', gridwidth=0.5, row=i, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgb(200, 200, 200)', gridwidth=0.5, row=i, col=1)
        
        self._update_axes(fig)
        
        # Display plot
        html = fig.to_html(include_plotlyjs='cdn', full_html=False)
        self.browser.setHtml(html)
        
    def _generate_subplot_titles(self, data: Dict) -> List[str]:
        """Generate subplot titles with value ranges"""
        components = ['H', 'D', 'Z', 'S']
        labels = ['Horizontal Intensity', 'Declination', 
                 'Vertical Intensity', 'Total Intensity']
        units = ['nT', 'minutes', 'nT', 'nT']
        
        titles = []
        for comp, label, unit in zip(components, labels, units):
            if comp in data:
                values = [x for x in data[comp] if x is not None]
                if values:
                    min_val = min(values)
                    max_val = max(values)
                    if comp == 'D':
                        min_val *= 60
                        max_val *= 60
                    titles.append(
                        f'{label} ({comp}) - Range: {min_val:.1f} '
                        f'to {max_val:.1f} {unit}'
                    )
                else:
                    titles.append(f'{label} ({comp})')
            else:
                titles.append(f'{label} ({comp})')
        
        return titles
        
    def _add_component_trace(self, fig, data: Dict, 
                           component: str, color: str, row: int):
        """Add a trace for a component to the figure"""
        values = [x if x is not None else np.nan for x in data[component]]
        if component == 'D':
            values = [x * 60 if x is not None else np.nan for x in values]
            
        fig.add_trace(
            go.Scatter(
                x=data['datetime'],
                y=values,
                name=component,
                line=dict(color=color, width=1),
                mode='lines+markers',
                marker=dict(size=2)
            ),
            row=row, col=1
        )
        
    def _update_axes(self, fig):
        """Update axes properties"""