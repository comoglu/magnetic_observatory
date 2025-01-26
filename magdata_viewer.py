#!/usr/bin/env python3
"""
Magnetic Observatory Data Viewer
A comprehensive tool for visualizing and analyzing geomagnetic data.
"""

# Standard library imports 
import sys
import os
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Optional

# Third-party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import aiohttp
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QBuffer, QIODevice
from PyQt5.QtWidgets import (
    QAction, QApplication, QDialog, QDialogButtonBox, QDockWidget, 
    QFileDialog, QHBoxLayout, QMainWindow, QMenuBar, QMessageBox,
    QStatusBar, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Local imports
from magnetic_observatory.utils.constants import STATION_INFO
from magnetic_observatory.utils.data_handlers import DataFetchHandler, DataProcessor, ExportHandler
from magnetic_observatory.ui.components import ControlPanel, DataTable, PlotPanel
from magnetic_observatory.ui.analysis_dialog import AnalysisDialog

class DataFetchWorker(QThread):
    """Worker thread for asynchronous data fetching"""
    data_ready = pyqtSignal(dict)
    kp_ready = pyqtSignal(list)  # Changed from dict to list
    error = pyqtSignal(str)
    
    def __init__(self, params: Dict, station_code: str):
        super().__init__()
        self.params = params
        self.station_code = station_code
    
    def run(self):
        """Execute the data fetching operation"""
        try:
            # Create fetch handler
            fetch_handler = DataFetchHandler(self.station_code)
            
            # Set up event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Fetch data
            data = loop.run_until_complete(fetch_handler.fetch_data(self.params))
            
            # Process data
            processor = DataProcessor(data, self.station_code)
            processed_data = processor.process_data()
            
            # Emit the processed data
            self.data_ready.emit(processed_data)
            
            # Fetch Kp index in the background
            kp_data = loop.run_until_complete(fetch_handler.fetch_kp_index())
            if isinstance(kp_data, list) and kp_data:
                self.kp_ready.emit(kp_data)
                
            loop.close()
            
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))


class MagneticDataViewer(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.current_station = None
        self.fetch_worker = None
        self.control_panel = None
        self.plot_panel = None
        self.data_table = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Magnetic Observatory Data Viewer")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Initialize control panel
        control_dock = QDockWidget("Controls", self)
        self.control_panel = ControlPanel(STATION_INFO)
        control_dock.setWidget(self.control_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, control_dock)
        
        # Connect control panel signals
        self.control_panel.station_select.currentTextChanged.connect(
            self.update_station_info
        )
        self.control_panel.fetch_btn.clicked.connect(self.fetch_data)
        
        # Initialize plot panel
        self.plot_panel = PlotPanel()
        main_layout.addWidget(self.plot_panel)
        
        # Initialize data table
        table_dock = QDockWidget("Data Table", self)
        self.data_table = DataTable()
        table_dock.setWidget(self.data_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, table_dock)

        # In MagneticDataViewer.init_ui
        control_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                                QDockWidget.DockWidgetFloatable)
        table_dock.setFeatures(QDockWidget.DockWidgetMovable | 
                            QDockWidget.DockWidgetFloatable)

        # Initialize menu
        self.init_menu()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def init_menu(self):
        """Initialize the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Export submenu
        export_menu = file_menu.addMenu('Export')

        export_csv = QAction('Export CSV', self)
        export_csv.triggered.connect(lambda: self.export_data('csv'))
        export_menu.addAction(export_csv)

        export_excel = QAction('Export Excel', self)
        export_excel.triggered.connect(lambda: self.export_data('excel'))
        export_menu.addAction(export_excel)

        export_pdf = QAction('Export PDF Report', self)
        export_pdf.triggered.connect(self.export_pdf)
        export_menu.addAction(export_pdf)
        
        # Exit action
        file_menu.addSeparator()
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Analysis menu
        analysis_menu = menubar.addMenu('Analysis')
        analyze_action = QAction('Analyze Data', self)
        analyze_action.triggered.connect(self.show_analysis)
        analysis_menu.addAction(analyze_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def fetch_data(self):
        """Initiate data fetching process"""
        try:
            self.control_panel.fetch_btn.setEnabled(False)
            self.statusBar().showMessage("Fetching data...")
            
            # Get station code
            station_text = self.control_panel.station_select.currentText()
            self.current_station = station_text[:3]
            
            # Prepare request parameters
            params = {
                "Request": "GetData",
                "format": "JSON",
                "testObsys": "0",
                "observatoryIagaCode": self.current_station,
                "samplesPerDay": self.control_panel.sample_rate.currentText(),
                "publicationState": self.control_panel.pub_state.currentText(),
                "dataStartDate": self.control_panel.calendar.selectedDate().toString("yyyy-MM-dd"),
                "dataDuration": self.control_panel.duration.value(),
                "orientation": self.control_panel.orientation.currentText()
            }
            
            # Create and start worker thread
            self.fetch_worker = DataFetchWorker(params, self.current_station)
            self.fetch_worker.data_ready.connect(self.handle_data)
            self.fetch_worker.kp_ready.connect(self.handle_kp_data)
            self.fetch_worker.error.connect(self.handle_error)
            self.fetch_worker.finished.connect(
                lambda: self.control_panel.fetch_btn.setEnabled(True)
            )
            self.fetch_worker.start()
            
        except Exception as e:
            self.handle_error(str(e))
            self.control_panel.fetch_btn.setEnabled(True)
            
    def handle_data(self, data: Dict):
        """Process received magnetic data"""
        try:
            self.current_data = data
            
            if not data or 'datetime' not in data:
                raise ValueError("Received invalid or empty data")
                
            self.plot_panel.update_plot(
                data, 
                self.control_panel.station_select.currentText()
            )
            self.data_table.update_data(data)
            
            self.statusBar().showMessage(
                f"Data fetched successfully - {len(data['datetime'])} samples", 
                5000
            )
            
        except Exception as e:
            self.handle_error(f"Failed to process data: {str(e)}")
            
    def handle_kp_data(self, kp_data: list):
        """Handle received Kp index data"""
        try:
            if isinstance(kp_data, list) and len(kp_data) > 1:
                # NOAA API returns a list where each item is [timestamp, kp_value]
                latest_entry = kp_data[-1]
                if len(latest_entry) >= 2:
                    latest_kp = latest_entry[1]
                    self.statusBar().showMessage(
                        f"Latest Kp index: {latest_kp}",
                        5000
                    )
        except Exception as e:
            print(f"Failed to process Kp data: {str(e)}")
            
    def handle_error(self, error_msg: str):
        """Display error message to user"""
        QMessageBox.critical(self, "Error", error_msg)
        self.statusBar().showMessage("Operation failed", 3000)
            
    def export_data(self, format_type: str):
        """Export data to file"""
        if not self.current_data:
            QMessageBox.warning(
                self,
                "Warning",
                "No data available for export."
            )
            return
                
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setDefaultSuffix(format_type)
            
            if format_type == 'csv':
                filename, _ = file_dialog.getSaveFileName(
                    self,
                    "Export CSV",
                    "",
                    "CSV files (*.csv)"
                )
            else:  # Excel
                filename, _ = file_dialog.getSaveFileName(
                    self,
                    "Export Excel",
                    "",
                    "Excel files (*.xlsx)"
                )
                        
            if filename:
                self.statusBar().showMessage(f"Exporting data to {format_type}...")
                
                # Prepare data for export
                export_data = {}
                for key in self.current_data:
                    if isinstance(self.current_data[key], (list, np.ndarray)):
                        # Convert numpy arrays to lists
                        values = (self.current_data[key].tolist() 
                                if isinstance(self.current_data[key], np.ndarray) 
                                else self.current_data[key])
                        # Handle NaN values
                        export_data[key] = [
                            '' if (isinstance(v, float) and np.isnan(v)) else v 
                            for v in values
                        ]
                
                if format_type == 'csv':
                    import csv
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # Write headers
                        headers = ['Time'] + [h for h in export_data.keys() if h != 'datetime']
                        writer.writerow(headers)
                        # Write data rows
                        for i in range(len(export_data['datetime'])):
                            row = [export_data['datetime'][i]]
                            for h in headers[1:]:
                                if i < len(export_data[h]):
                                    row.append(export_data[h][i])
                                else:
                                    row.append('')
                            writer.writerow(row)
                else:  # Excel
                    import pandas as pd
                    df = pd.DataFrame(export_data)
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Magnetic Data')
                        
                self.statusBar().showMessage(
                    f"Data exported successfully to {filename}",
                    3000
                )
                    
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export data: {str(e)}"
            )
            self.statusBar().showMessage("Export failed", 3000)

    def export_pdf(self):
        if not self.current_data:
            QMessageBox.warning(self, "Warning", "No data available for export.")
            return
            
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export PDF",
                "",
                "PDF files (*.pdf)"
            )
            
            if filename:
                self.statusBar().showMessage("Generating INTERMAGNET report...")
                from utils.report_generator import IntermagnetReportGenerator
                generator = IntermagnetReportGenerator(self.current_data, self.current_station)
                generator.generate_report(filename)
                self.statusBar().showMessage(f"INTERMAGNET report exported successfully to {filename}", 3000)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
            self.statusBar().showMessage("Report export failed", 3000)

    def show_analysis(self):
        """Display the analysis dialog"""
        if not self.current_data:
            QMessageBox.warning(
                self,
                "Warning",
                "Please fetch data before performing analysis."
            )
            return
            
        try:
            dialog = AnalysisDialog(
                self.current_data,
                self.current_station,
                self
            )
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to perform analysis: {str(e)}"
            )
            
    def update_station_info(self):
        """Update the station information display"""
        try:
            station_code = self.control_panel.station_select.currentText()[:3]
            self.current_station = station_code
            
            if station_code in STATION_INFO:
                station = STATION_INFO[station_code]
                info = (
                    f"Name: {station['name']}, {station['country']}\n"
                    f"Location: {station['latitude']}°N, {station['longitude']}°E\n"
                    f"Elevation: {station['elevation']}m\n"
                    f"Institute: {station['institute']}\n"
                    f"Orientation: {station['orientation']}"
                )
                self.control_panel.station_info_display.setText(info)
                
        except Exception as e:
            self.handle_error(f"Failed to update station info: {str(e)}")
            
    def show_about(self):
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtWidgets import QVBoxLayout, QLabel, QDialog

        dialog = QDialog(self)
        dialog.setWindowTitle("About")
        layout = QVBoxLayout()

        about_text = """
        <h2>Magnetic Observatory Data Viewer</h2>
        <p>Created by Mustafa Comoglu<br>
        <a href="https://github.com/comoglu">https://github.com/comoglu</a></p>
        <p>Version 0.4</p>
        <p>Features:</p>
        <ul>
            <li>Real-time data fetching from INTERMAGNET</li>
            <li>Interactive plots with multiple components</li>
            <li>Advanced data analysis tools</li>
            <li>Data quality assessment</li>
            <li>Magnetic disturbance detection</li>
            <li>Export capabilities (CSV, Excel,PDF)</li>
        </ul>
        <p>Data provided by INTERMAGNET through BGS GIN Services.</p>
        """

        label = QLabel(about_text)
        label.setOpenExternalLinks(True)
        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.exec_() 

    def closeEvent(self, event):
        """Handle application closure"""
        try:
            if self.fetch_worker and self.fetch_worker.isRunning():
                self.fetch_worker.terminate()
                self.fetch_worker.wait()
            event.accept()
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            event.accept()


def main():
    """Application entry point"""
    try:
        app = QApplication(sys.argv)
        viewer = MagneticDataViewer()
        viewer.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
