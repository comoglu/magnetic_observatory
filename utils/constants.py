# utils/constants.py

STATION_INFO = {
    "IZN": {
        "name": "Iznik",
        "country": "Turkey",
        "institute": "Kandilli Observatory and Earthquake Research Institute",
        "latitude": 40.5,
        "longitude": 29.7,
        "elevation": 0,
        "orientation": "HDZS"
    },
    "ISK": {
        "name": "Istanbul",
        "country": "Turkey",
        "institute": "Kandilli Observatory and Earthquake Research Institute",
        "latitude": 41.063,
        "longitude": 29.062,
        "elevation": 130,
        "orientation": "HDZS"
    },
    "ASP": {
        "name": "Alice Springs",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -23.762,
        "longitude": 133.883,
        "elevation": 557,
        "orientation": "XYZS"
    },
    "CKI": {
        "name": "Cocos (Keeling) Islands",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -12.188,
        "longitude": 96.834,
        "elevation": 3,
        "orientation": "XYZS"
    },
    "CNB": {
        "name": "Canberra",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -35.32,
        "longitude": 149.36,
        "elevation": 859,
        "orientation": "XYZS"
    },
    "CTA": {
        "name": "Charters Towers",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -20.09,
        "longitude": 146.264,
        "elevation": 370,
        "orientation": "XYZS"
    },
    "GNA": {
        "name": "Gnangara",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -31.78,
        "longitude": 115.947,
        "elevation": 60,
        "orientation": "XYZS"
    },
    "GNG": {
        "name": "Gingin",
        "country": "Australia", 
        "institute": "Geoscience Australia",
        "latitude": -31.356,
        "longitude": 115.715,
        "elevation": 50,
        "orientation": "XYZS"
    },
    "KDU": {
        "name": "Kakadu",
        "country": "Australia",
        "institute": "Geoscience Australia", 
        "latitude": -12.69,
        "longitude": 132.47,
        "elevation": 15,
        "orientation": "XYZS"
    },
    "LRM": {
        "name": "Learmonth",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -22.22,
        "longitude": 114.1,
        "elevation": 4,
        "orientation": "XYZS"
    },
    "MAW": {
        "name": "Mawson",
        "country": "Antarctica",
        "institute": "Geoscience Australia",
        "latitude": -67.6,
        "longitude": 62.88,
        "elevation": 12,
        "orientation": "XYZS"
    },
    "MCQ": {
        "name": "Macquarie Island",
        "country": "Australia",
        "institute": "Geoscience Australia",
        "latitude": -54.5,
        "longitude": 158.95,
        "elevation": 4,
        "orientation": "XYZS"
    }
}

DATA_ORIENTATIONS = ['XYZS', 'HDZS']

PUBLICATION_STATES = [
    'reported',
    'adjusted', 
    'quasi-def',
    'definitive',
    'best-avail'
]

SAMPLING_RATES = ['PT1M', 'PT1S']  # Minute, Second

# Quality control parameters
QC_PARAMS = {
    'max_gap_minutes': 5,
    'spike_threshold': 3.0,  # Standard deviations
    'baseline_jump_threshold': 3.0,  # Standard deviations
    'minimum_samples': 60  # Minimum samples for valid analysis
}