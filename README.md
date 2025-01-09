# Route Fuel Station Finder

A Python tool that analyzes driving routes and finds nearby fuel stations (Love's and Pilot) with current diesel prices. The tool uses Google Maps API for route data and MongoDB for fuel station information.  The tool compared two different algorithms for finding fuel stations within a certain radius of the route: (1) KDTree and (2) GeoPandas. 

**KDTree** was determined to be the faster algorithm with lower memory use. KDTree is almost 50 times faster than GeoPandas for the tests for cross country routes searching through 1,500 possible fuel stations. 

## Features

- Finds fuel stations within a specified distance of any driving route
- Shows current diesel prices at each station
- Creates interactive HTML maps showing:
  - The driving route
  - Nearby stations (green markers)
  - Other stations (red markers)
- Compares two search algorithms:
  - GeoPandas-based spatial search
  - KD-Tree-based search with route interpolation
- Provides detailed route analysis and performance metrics

## Requirements

- Python 3.8+
- MongoDB database with fuel station data
- Google Maps API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository
2. Install required packages: `pip install -r requirements.txt`

3. Create a `.env` file with your credentials.  The MongoDB contains the fuel station locations and fuel prices.  Google Maps is needed for getting driving routes.
```bash
DB_URL=your_mongodb_url
DB_NAME=your_database_name
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## Usage

Basic usage with default parameters:
```bash
python main.py --start "Starting Address" --end "Ending Address"
```

### Parameters

- `--start`: Starting address (default: Empire State Building, NYC)
- `--end`: Ending address (default: Metropolitan Museum of Art, NYC)
- `--distance`: Search radius in miles (default: 1.0)
- `--simplify`: Route simplification tolerance in degrees (default: 0.0002)
  - 0.0002 ≈ 22m accuracy
  - 0.0001 ≈ 11m accuracy
  - 0.0004 ≈ 44m accuracy

## Example
```bash
python main.py --start "New York, NY" --end "Los Angeles, CA" --distance 1.0
```
This command will:
1. Validate the addresses
2. Generate a driving route
3. Simplify the route (reducing points while maintaining accuracy)
4. Find fuel stations within 1 mile of the route
5. Create interactive maps
6. Compare search algorithm performance

Example output:
```bash
Command Line Arguments:
+----------------------+-----------------+
| Parameter            | Value           |
|----------------------+-----------------|
| Start Location       | New York, NY    |
| End Location         | Los Angeles, CA |
| Search Distance      | 1.0 miles       |
| Route Simplification | 0.0002 degrees  |
+----------------------+-----------------+

Validated location: New York, NY, USA
Validated location: Los Angeles, CA, USA

Simplifying route from 213092 points...
Using tolerance of 0.0002 degrees (≈22m)
This means any point that deviates less than this distance from the simplified 
route will be removed while preserving the overall route shape.
Route simplified to 4151 points
Reduction: 98.1%

Route Analysis:
+---------------------+----------+
| Metric              |    Value |
|---------------------+----------|
| Total Points        |  4151.00 |
| Avg Distance (m)    |  1080.84 |
| Min Distance (m)    |     2.38 |
| Max Distance (m)    | 22138.13 |
| Std Dev (m)         |  1600.27 |
| Total Distance (km) |  4485.47 |
| Total Distance (mi) |  2787.15 |
+---------------------+----------+

Fuel Location Validation Results:
Total locations: 1440
Valid locations: 1439
Invalid locations: 1

Invalid Location Details:
+---------------+-----------------+-------+-------+
| Location ID   | Address         |   Lat |   Lon |
|---------------+-----------------+-------+-------|
| pilot_7996    | N/A, Monroe, NC |   nan |   nan |
+---------------+-----------------+-------+-------+

Testing GeoPandas search method...
  Creating map with route and fuel stations: route_map_GeoPandas.html

Testing KDTree search method...
  Creating map with route and fuel stations: route_map_KDTree.html

Method Comparison Results:
+-------------------+-------------+----------+
| Metric            |   GeoPandas |   KDTree |
|-------------------+-------------+----------|
| Time (s)          |       0.336 |    0.081 |
| Memory (MB)       |       7.766 |    0.172 |
| Total Stations    |          77 |       77 |
| Matching Stations |          77 |       77 |
| Unique Stations   |           0 |        0 |
+-------------------+-------------+----------+


Found 77 fuel stations within 1.0 miles of route. Showing first 10:
+---------------+-----------------------------------------------+----------------+------------+-------------+
| Location ID   | Address                                       | Diesel Price   |   Latitude |   Longitude |
|---------------+-----------------------------------------------+----------------+------------+-------------|
| loves_374     | 2974 Lenwood Rd., Barstow, CA 92311           | $4.949         |    34.8571 |   -117.092  |
| loves_649     | 1015 Hospital Rd, Brush, CO 80723             | $3.849         |    40.2661 |   -103.639  |
| loves_517     | 748 22 Road, Grand Junction, CO 81505         | $4.089         |    39.1142 |   -108.646  |
| loves_377     | 201 East Bison Hwy, Hudson, CO 80642          | $3.479         |    40.077  |   -104.649  |
| loves_826     | 100 E Cardinal Way Ste A, Parachute, CO 81635 | $3.649         |    39.4555 |   -108.044  |
| loves_411     | 11820 Hickman Road, Clive, IA 50325           | $3.489         |    41.6134 |    -93.7807 |
| loves_361     | 4400 S. 22nd Ave. E., Newton , IA 50208       | $3.689         |    41.6804 |    -92.9991 |
| loves_426     | 10 East Street, Shelby, IA 51570              | $3.689         |    41.497  |    -95.4519 |
| loves_766     | 5 South State Street, Atkinson, IL 61235      | $3.589         |    41.4106 |    -90.0163 |
| loves_859     | 8909 N Brisbin Rd, Morris, IL 60450           | $3.889         |    41.4153 |    -88.3656 |
+---------------+-----------------------------------------------+----------------+------------+-------------+
```


## Output Files

The tool generates two interactive HTML maps:
- `route_map_GeoPandas.html`: Results from GeoPandas-based search
- `route_map_KDTree.html`: Results from KD-Tree-based search

Each map shows:
- The complete route (blue line)
- Nearby fuel stations (green markers)
- Other fuel stations (red markers)
- Popup information for each station including:
  - Location ID
  - Address
  - Current diesel price

## Algorithm Comparison

The tool implements and compares two search algorithms:

1. **GeoPandas Spatial Search**
   - Uses GeoPandas for spatial operations
   - Creates a buffer around the route
   - Finds stations within the buffer using spatial indexing

2. **KD-Tree Search**
   - Uses scipy's cKDTree for efficient nearest neighbor search
   - Interpolates route points for better coverage
   - Batches queries for memory efficiency

Performance metrics show:
- Execution time
- Memory usage
- Number of stations found
- Result consistency between methods