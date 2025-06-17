# MetroBusRoutePlanner 🚍

![Metro Bus](https://via.placeholder.com/800x200?text=Islamabad+Metro+Bus+Route+Planner)

A smart route planning tool for the Islamabad-Rawalpindi Metro Bus system, providing optimal routing between any two stations using advanced geospatial algorithms.

## Table of Contents 📑
- [Features](#-features)
- [Technologies](#-technologies-used)
- [Installation](#-installation)
- [Usage](#-usage)
- [Data Structure](#-data-structure)
- [Algorithm](#-algorithm-details)
- [Future Work](#-future-work)
- [Contributing](#-contributing)
- [License](#-license)

## 🔍 Features

### Core Functionality
- 🗺️ **Interactive Route Planning**: Find the shortest path between any two stations
- ⏱️ **Travel Time Estimates**: Accurate time calculations including transfer waits
- 💰 **Fare Calculation**: Estimated trip cost based on distance
- 🔄 **Smart Transfers**: Automatic detection of interchange stations

### Technical Features
- Geospatial network modeling with precise coordinates
- Multi-line support (Red, Blue, Green, Yellow BRT lines)
- Graph-based pathfinding with weighted edges
- Responsive web interface with mobile-friendly design

## 🚀 Technologies Used

| Category        | Technologies                          |
|-----------------|---------------------------------------|
| Backend         | Python 3.9+, NetworkX, GeoPandas     |
| Geospatial      | QGIS, PostGIS, geopy (geodesic)      |
| Database        | PostgreSQL with PostGIS extension    |
| Frontend        | Streamlit, Leaflet.js (for maps)     |
| DevOps          | Docker, GitHub Actions               |

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 12+ with PostGIS
- QGIS (for data preparation)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Daniyal1234-alt/MetroBusRoutePlanner.git
   cd MetroBusRoutePlanner
2. **Set up a Python environment and install dependencies**:
   ```bash
    pip install -r requirements.txt
    cd
3. **Start the Streamlit app**:
   ```bash
    streamlit run app.py
4. **Ensure PostgreSQL and PostGIS are installed and properly configured. Import the provided network data into your database if included.**

📍 ### Future Work
Add real-time traffic updates or delays
Expand to other cities with similar BRT systems
Mobile-friendly UI for field usage

### Research Areas
Machine learning for demand prediction
Alternative routing algorithms (A*, Yen's)
Accessibility features for special needs

### Contact:
daniyalaziz184@gmail.com
