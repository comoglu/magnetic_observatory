# Magnetic Observatory Data Viewer

A comprehensive Python application for visualizing and analyzing geomagnetic data from Turkish and Australian observatories.
![magdata_viewer](https://github.com/user-attachments/assets/2ca3e9ef-bc94-44fa-b1de-f23ab6ccc7f7)


## Features

- Real-time data fetching from INTERMAGNET through BGS GIN Services
- Interactive visualization of magnetic field components (H, D, Z, F)
- Advanced data analysis tools:
  - FFT Analysis
  - Disturbance Detection (Sudden Storm Commencements, Substorms)
  - Quality Control
  - Statistical Analysis
- Support for multiple data orientations (XYZ, HDZ)
- Export capabilities (CSV, Excel)
- K-index monitoring and alerts

## Installation

```bash
# Clone the repository
git clone https://github.com/comoglu/magnetic_observatory.git
cd magnetic_observatory

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Dependencies

- Python 3.8+
- PyQt5
- plotly
- numpy
- pandas
- scipy
- aiohttp
- xlsxwriter

## Usage

Run the main application:

```bash
python magdata_viewer.py
```

1. Select a magnetic observatory from the dropdown menu
2. Choose your data parameters:
   - Date range
   - Sample rate (Minute/Second)
   - Publication state
   - Data orientation
3. Click "Fetch Data" to retrieve and visualize the data

## Data Analysis

The application provides four main analysis tabs:

1. **FFT Analysis**: Frequency analysis of magnetic components
2. **Disturbance Analysis**: Detection of magnetic storms and events
3. **Quality Analysis**: Data quality metrics and gap detection
4. **Statistics**: Statistical analysis and coordinate transformations

## Supported Observatories

### Turkey
- IZN (Iznik)
- ISK (Istanbul)

### Australia
- ASP (Alice Springs)
- CKI (Cocos Islands)
- CNB (Canberra)
- CTA (Charters Towers)
- GNA (Gnangara)
- GNG (Gingin)
- KDU (Kakadu)
- LRM (Learmonth)
- MAW (Mawson)
- MCQ (Macquarie Island)

## Code Structure

```
magnetic_observatory/
├── magdata_viewer.py       # Main application
├── utils/
│   ├── constants.py        # Configuration constants
│   ├── data_handlers.py    # Data processing utilities
│   └── logging_config.py   # Logging configuration
├── analyzers/
│   ├── base_analyzer.py    # Base analysis class
│   ├── disturbance.py      # Disturbance detection
│   ├── orientation.py      # Coordinate transformations
│   └── quality.py          # Quality control
└── ui/
    ├── components.py       # UI components
    └── analysis_dialog.py  # Analysis interface
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Data provided by [INTERMAGNET](http://www.intermagnet.org/)
- BGS Geomagnetism Information Node Services
- Kandilli Observatory and Earthquake Research Institute
- Geoscience Australia

## Contact

For questions and support:
- Email: comoglu AT gmail.com
- GitHub: [@comoglu](https://github.com/comoglu)
