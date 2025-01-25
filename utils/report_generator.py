from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import os
import kaleido
import pandas as pd
from magnetic_observatory.analyzers.disturbance import DisturbanceAnalyzer
from magnetic_observatory.analyzers.quality import QualityAnalyzer
from magnetic_observatory.analyzers.orientation import OrientationAnalyzer
from magnetic_observatory.utils.constants import STATION_INFO

class IntermagnetReportGenerator:
    def __init__(self, data, station_code):
        self.data = data
        self.station_code = station_code
        self.station_info = STATION_INFO.get(station_code, {})
        self.styles = getSampleStyleSheet()
        self.initialize_analyzers()

    def initialize_analyzers(self):
        self.disturbance_analyzer = DisturbanceAnalyzer(self.data, self.station_code)
        self.quality_analyzer = QualityAnalyzer(self.data, self.station_code)
        self.orientation_analyzer = OrientationAnalyzer(self.data, self.station_code)

    def generate_report(self, output_path):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []
        with tempfile.TemporaryDirectory() as temp_dir:
            # Cover page
            self._add_cover_page(story)
            story.append(PageBreak())

            # Station information & Maps
            self._add_station_info(story)
            self._add_maps(story, temp_dir)
            story.append(PageBreak())

            # Data overview
            self._add_data_overview(story, temp_dir)
            story.append(PageBreak())

            # Quality analysis
            self._add_quality_analysis(story, temp_dir)
            story.append(PageBreak())

            # Magnetic disturbance analysis
            self._add_disturbance_analysis(story, temp_dir)
            story.append(PageBreak())

            # Baseline analysis
            self._add_baseline_analysis(story, temp_dir)
            story.append(PageBreak())

            # Appendix with technical details
            self._add_technical_appendix(story)

            doc.build(story)

    def _add_cover_page(self, story):
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("INTERMAGNET Observatory Report", title_style))
        story.append(Spacer(1, 30))
        
        station_text = f"{self.station_code} - {self.station_info.get('name', '')}"
        date_range = f"Report Period: {self.data['datetime'][0]} to {self.data['datetime'][-1]}"
        
        story.append(Paragraph(station_text, self.styles['Heading2']))
        story.append(Paragraph(date_range, self.styles['Heading3']))
        story.append(Spacer(1, 50))
        
        gen_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Report Generated: {gen_date}", self.styles['Normal']))
        story.append(Paragraph(f"Report Version: 2.0", self.styles['Normal']))
        story.append(Paragraph("INTERMAGNET Observatory Network", self.styles['Normal']))

    def _add_station_info(self, story):
        story.append(Paragraph("Station Information", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        info_data = [
            ['Parameter', 'Value'],
            ['IAGA Code', self.station_code],
            ['Station Name', self.station_info.get('name', '')],
            ['Country', self.station_info.get('country', '')],
            ['Geographic Latitude', f"{self.station_info.get('latitude', '')}°"],
            ['Geographic Longitude', f"{self.station_info.get('longitude', '')}°"],
            ['Elevation', f"{self.station_info.get('elevation', '')} m"],
            ['Institute', self.station_info.get('institute', '')],
            ['Data Orientation', self.station_info.get('orientation', '')]
        ]
        
        table = Table(info_data, colWidths=[200, 300])
        table.setStyle(self._get_table_style())
        story.append(table)

    def _add_maps(self, story, temp_dir):
        story.append(Spacer(1, 20))
        story.append(Paragraph("Observatory Location", self.styles['Heading2']))
        
        lat = self.station_info['latitude']
        lon = self.station_info['longitude']
        name = f"{self.station_code} - {self.station_info['name']}"
        
        fig = go.Figure(go.Scattergeo(
            lon=[lon],
            lat=[lat],
            text=[name],
            mode='markers+text',
            marker=dict(size=15, color='red'),
            textposition="top center"
        ))
        
        fig.update_geos(
            scope='world',
            projection_type='equirectangular',
            showcoastlines=True,
            coastlinecolor='rgb(80, 80, 80)',
            coastlinewidth=0.5,
            showland=True,
            landcolor='rgb(243, 243, 243)',
            showocean=True,
            oceancolor='rgb(204, 229, 255)',
            showcountries=True,
            countrycolor='rgb(80, 80, 80)',
            countrywidth=0.5,
            showframe=False,
            resolution=50,
            lataxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgb(102, 102, 102)',
            ),
            lonaxis=dict(
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgb(102, 102, 102)', 
            )
        )
        
        fig.update_layout(
            title=f"Location of {self.station_code} Observatory",
            height=600,
            width=800,
            margin=dict(l=0, r=0, t=30, b=0),
            geo=dict(
                center=dict(lon=lon, lat=lat),
                projection=dict(scale=2)
            )
        )
        
        map_path = os.path.join(temp_dir, 'location_map.png')
        self._save_plot(fig, map_path)
        story.append(Image(map_path, width=7*inch, height=5*inch))
        story.append(Spacer(1, 12))

    def _add_data_overview(self, story, temp_dir):
        story.append(Paragraph("Data Overview", self.styles['Heading1']))
        story.append(Spacer(1, 12))
        
        fig = self._create_timeseries_plot()
        plot_path = os.path.join(temp_dir, 'timeseries.png')
        self._save_plot(fig, plot_path)
        story.append(Image(plot_path, width=7*inch, height=5*inch))
        
        story.append(Spacer(1, 12))
        story.append(Paragraph("Data Statistics", self.styles['Heading2']))
        
        stats_data = self._calculate_statistics()
        stats_table = Table(stats_data, colWidths=[100, 100, 100, 100, 100])
        stats_table.setStyle(self._get_table_style())
        story.append(stats_table)

    def _add_quality_analysis(self, story, temp_dir):
        story.append(Paragraph("Data Quality Analysis", self.styles['Heading1']))
        
        # Get quality metrics
        metrics = self.quality_analyzer.get_quality_metrics()
        
        if metrics:
            fig = self._create_quality_plot(metrics)
            plot_path = os.path.join(temp_dir, 'quality.png')
            self._save_plot(fig, plot_path)
            story.append(Image(plot_path, width=7*inch, height=4*inch))
        
        # Add data gaps analysis
        gaps = self.quality_analyzer.analyze_data_gaps()
        if gaps:
            story.append(Paragraph("Data Gaps", self.styles['Heading2']))
            gap_data = [['Start Time', 'End Time', 'Duration']]
            for gap in gaps[:10]:
                gap_data.append([
                    str(gap['start_time']),
                    str(gap['end_time']),
                    str(gap['duration'])
                ])
            gap_table = Table(gap_data, colWidths=[200, 200, 100])
            gap_table.setStyle(self._get_table_style())
            story.append(gap_table)

    def _create_timeseries_plot(self):
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('H Component', 'D Component', 'Z Component', 'F Component'),
            shared_xaxes=True,
            vertical_spacing=0.08
        )
        
        # Convert datetime strings to numpy datetime64
        datetime_array = np.array([np.datetime64(t) for t in self.data['datetime']])
        
        components = ['H', 'D', 'Z', 'F']
        colors = ['red', 'green', 'blue', 'black']
        
        for i, (comp, color) in enumerate(zip(components, colors), 1):
            if comp in self.data:
                values = np.array([x if x is not None else np.nan for x in self.data[comp]])
                if comp == 'D':
                    values = values * 60  # Convert to minutes
                
                fig.add_trace(
                    go.Scatter(
                        x=datetime_array,
                        y=values,
                        name=comp,
                        line=dict(color=color, width=1)
                    ),
                    row=i, col=1
                )
        
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Magnetic Components Time Series"
        )
        
        return fig

    def _create_quality_plot(self, metrics):
        components = list(metrics.keys())
        metrics_list = ['completeness', 'noise_level', 'stability']
        
        fig = go.Figure()
        
        for comp in components:
            values = [metrics[comp][metric] for metric in metrics_list]
            fig.add_trace(go.Bar(
                name=comp,
                x=metrics_list,
                y=values
            ))
        
        fig.update_layout(
            title='Data Quality Metrics by Component',
            barmode='group',
            xaxis_title='Metric',
            yaxis_title='Value'
        )
        
        return fig

    def _add_disturbance_analysis(self, story, temp_dir):
       story.append(Paragraph("Magnetic Disturbance Analysis", self.styles['Heading1']))
       
       k_indices = self.disturbance_analyzer.calculate_k_index()
       if k_indices:
           story.append(Paragraph("K-index Values", self.styles['Heading2']))
           k_data = [['Start Time', 'End Time', 'K-value', 'Variation (nT)']]
           for k in k_indices[:24]:  # Show 24 hours worth
               k_data.append([
                   str(k['start_time']),
                   str(k['end_time']),
                   str(k['k_value']),
                   f"{k['variation']:.1f}"
               ])
           k_table = Table(k_data, colWidths=[150, 150, 100, 100])
           k_table.setStyle(self._get_table_style())
           story.append(k_table)
       
       disturbed_periods = self.disturbance_analyzer.find_disturbed_periods()
       if disturbed_periods:
           story.append(Spacer(1, 12))
           story.append(Paragraph("Disturbed Periods", self.styles['Heading2']))
           
           fig = self._create_disturbance_plot(disturbed_periods)
           plot_path = os.path.join(temp_dir, 'disturbance.png')
           self._save_plot(fig, plot_path)
           story.append(Image(plot_path, width=7*inch, height=4*inch))

    def _add_baseline_analysis(self, story, temp_dir):
       story.append(Paragraph("Baseline Analysis", self.styles['Heading1']))
       
       stability = self.quality_analyzer.check_baseline_stability()
       
       if stability:
           for component, jumps in stability.items():
               story.append(Paragraph(f"{component} Component Baseline", self.styles['Heading2']))
               if jumps:
                   jump_data = [['Time', 'Magnitude (nT)']]
                   for jump in jumps[:10]:  # Show top 10 jumps
                       jump_data.append([
                           str(jump['time']),
                           f"{jump['magnitude']:.2f}"
                       ])
                   jump_table = Table(jump_data, colWidths=[200, 100])
                   jump_table.setStyle(self._get_table_style())
                   story.append(jump_table)
               story.append(Spacer(1, 12))

    def _add_technical_appendix(self, story):
       story.append(Paragraph("Technical Appendix", self.styles['Heading1']))
       
       # Data processing information
       story.append(Paragraph("Data Processing Information", self.styles['Heading2']))
       processing_info = [
           ['Parameter', 'Value'],
           ['Processing Date', datetime.now().strftime("%Y-%m-%d")],
           ['Software Version', '2.0'],
           ['Quality Control Level', 'Definitive'],
           ['Processing Steps', 'Spike detection, gap analysis, baseline stability check']
       ]
       proc_table = Table(processing_info, colWidths=[200, 300])
       proc_table.setStyle(self._get_table_style())
       story.append(proc_table)
       
       # Add QC parameters
       story.append(Spacer(1, 12))
       story.append(Paragraph("Quality Control Parameters", self.styles['Heading2']))
       qc_info = [
           ['Parameter', 'Threshold'],
           ['Spike Detection', '3σ'],
           ['Minimum Samples', '60'],
           ['Gap Definition', '> 5 minutes'],
           ['Baseline Jump', '3σ']
       ]
       qc_table = Table(qc_info, colWidths=[200, 300])
       qc_table.setStyle(self._get_table_style())
       story.append(qc_table)

    def _create_disturbance_plot(self, disturbances):
        fig = go.Figure()
        
        components = ['H', 'D', 'Z']
        colors = ['red', 'green', 'blue']
        
        for comp, color in zip(components, colors):
            comp_dist = [d for d in disturbances if d['component'] == comp]
            if comp_dist:
                times = [np.datetime64(d['start_time']) for d in comp_dist]
                deviations = [d['max_deviation'] for d in comp_dist]
                fig.add_trace(go.Scatter(
                    x=times,
                    y=deviations,
                    mode='markers',
                    name=f'{comp} Component',
                    marker=dict(color=color, size=8)
                ))
        
        fig.update_layout(
            title='Magnetic Disturbances',
            xaxis_title='Time',
            yaxis_title='Maximum Deviation (σ)',
            height=400
        )
        
        return fig

    def _calculate_statistics(self):
        stats = [['Component', 'Mean', 'Std Dev', 'Min', 'Max']]
        
        for comp in self.quality_analyzer.get_available_components():
            try:
                data = self.quality_analyzer.get_component_data(comp)
                stats.append([
                    comp,
                    f"{np.nanmean(data):.2f}",
                    f"{np.nanstd(data):.2f}",
                    f"{np.nanmin(data):.2f}",
                    f"{np.nanmax(data):.2f}"
                ])
            except ValueError:
                continue
                
        return stats

    def _get_table_style(self):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black)
        ])

    def _save_plot(self, fig, path):
        try:
            fig.write_image(path, scale=2)
        except Exception as e:
            print(f"Failed to save plot at high resolution: {e}")
            try:
                # Fallback to lower resolution
                fig.write_image(path, scale=1)
            except Exception as e:
                print(f"Failed to save plot: {e}")
                raise