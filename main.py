# Standard library imports
import os
import gc
import argparse
from time import time

# Route search and creation functions
from geopandas_search import find_fuel_stations_geopandas
from kdtree_search import find_fuel_stations_kdtree
from map_visualization import create_route_map
from route_analysis import get_route_points, analyze_route_spacing, validate_address

import googlemaps
from fuel_data import get_fuel_locations_with_prices
from dotenv import load_dotenv
import psutil
from tabulate import tabulate

# Debug imports (commented out)
# from pprint import pprint
# from memory_profiler import profile


def load_config():
    """Load environment variables"""
    load_dotenv()
    return {
        'db_url': os.getenv('DB_URL'),
        'db_name': os.getenv('DB_NAME'),
        'google_maps_api_key': os.getenv('GOOGLE_MAPS_API_KEY')
    }


def measure_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024.0 / 1024.0  # Convert bytes to MB


def test_search_method(route_points, fuel_locations, method_name, search_method, distance_miles=1.0):
    """Test a single search method and measure its performance

    Args:
        route_points (list): List of route points
        fuel_locations (list): List of fuel station locations
        method_name (str): Name of the search method being tested
        search_method (callable): The search method function to test
        distance_miles (float): Search radius in miles

    Returns:
        tuple: (stations, performance_metrics)
            - stations: List of found stations
            - performance_metrics: Dict containing time and memory usage
    """
    print(f"\nTesting {method_name} search method...")

    # Force garbage collection before test
    gc.collect()

    # Record baseline memory
    baseline_memory = measure_memory_usage()

    # Time the method
    start_time = time()
    stations = search_method(route_points, fuel_locations, distance_miles)
    end_time = time()

    # Record peak memory and force garbage collection
    peak_memory = measure_memory_usage()
    gc.collect()

    # Calculate performance metrics
    performance = {
        'time': end_time - start_time,
        'memory': peak_memory - baseline_memory,
        'count': len(stations)
    }

    # Create map for this method
    map_file_name = f'route_map_{method_name}.html'
    print(f"  Creating map with route and fuel stations: {map_file_name}")
    create_route_map(
        route_points,
        'Start Point',
        'End Point',
        stations,
        fuel_locations,
        map_file_name
    )

    return stations, performance


def print_fuel_station_table(stations, title=None):
    """Print a formatted table of fuel stations.

    Args:
        stations (list): List of station dictionaries containing location and price info
        title (str, optional): Title to print above the table
    """
    if title:
        print(f"\n{title}")

    table_data = [
        {
            'Location ID': station['locationId'],
            'Address': station['address'],
            'Diesel Price': f"${station['dieselPrice']}" if station.get('dieselPrice') != 'N/A' else 'N/A',
            'Latitude': station['lat'],
            'Longitude': station.get('lon', station.get('lng'))  # Handle both 'lon' and 'lng' keys
        } for station in stations
    ]
    print(tabulate(table_data, headers='keys', tablefmt='psql'))


def parse_arguments():
    """Parse command line arguments with defaults"""
    parser = argparse.ArgumentParser(
        description="""
        Route Analysis Tool for Fuel Stations
        
        This tool analyzes a route between two points and finds nearby fuel stations (Loves/Pilot).
        It provides:
        - Detailed route analysis with point spacing metrics
        - Nearby fuel stations within specified distance of route
        - Current diesel prices at each station
        - Interactive map showing route and stations
        - Performance comparison of different search methods
        
        The output includes:
        1. Route statistics (total points, distances between points)
        2. List of fuel stations near route with current prices
        3. Interactive HTML map with route and stations marked
        4. Search method performance metrics
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--start',
        default="20 W 34th St., New York, NY 10001",
        help='Starting point address (default: Empire State Building)'
    )

    parser.add_argument(
        '--end',
        default="1000 5th Ave, New York, NY 10028",
        help='Ending point address (default: Metropolitan Museum of Art)'
    )

    parser.add_argument(
        '--distance',
        type=float,
        default=1.0,
        help='Maximum distance (in miles) to search for fuel stations from route'
    )

    parser.add_argument(
        '--simplify',
        type=float,
        default=0.0002,
        help='Tolerance for route simplification in degrees. Higher values = fewer points. '
             '0.0002 ≈ 22m, 0.0001 ≈ 11m, 0.0004 ≈ 44m'
    )

    args = parser.parse_args()

    # Print argument summary as a table
    print("\nCommand Line Arguments:")
    table_data = [
        ["Parameter", "Value"],
        ["Start Location", args.start],
        ["End Location", args.end],
        ["Search Distance", f"{args.distance} miles"],
        ["Route Simplification", f"{args.simplify} degrees"]
    ]
    print(tabulate(table_data, headers="firstrow", tablefmt="psql"))
    print()

    return args


def main():
    args = parse_arguments()
    config = load_config()

    # Initialize Google Maps client once
    gmaps = googlemaps.Client(key=config['google_maps_api_key'])

    # Validate start and end addresses
    start_formatted = validate_address(gmaps, args.start)
    end_formatted = validate_address(gmaps, args.end)
    if not start_formatted or not end_formatted:
        return

    # Get route points using same client
    route_points = get_route_points(
        gmaps,
        start_formatted,
        end_formatted,
        detailed=True,
        simplify_tolerance=args.simplify
    )
    analyze_route_spacing(route_points, print_analysis=True)

    # Get valid fuel locations with prices
    valid_locations = get_fuel_locations_with_prices(config['db_url'], config['db_name'])

    # Print first 10 locations for verification
    # print_fuel_station_table(valid_locations[:10], title="First 10 valid locations (with prices):")

    # Test each search method separately
    geopandas_stations, geopandas_perf = test_search_method(
        route_points,
        valid_locations,
        "GeoPandas",
        find_fuel_stations_geopandas,
        args.distance
    )

    kdtree_stations, kdtree_perf = test_search_method(
        route_points,
        valid_locations,
        "KDTree",
        find_fuel_stations_kdtree,
        args.distance
    )

    # Get station IDs for comparison
    geopandas_ids = {s['locationId'] for s in geopandas_stations}
    kdtree_ids = {s['locationId'] for s in kdtree_stations}

    # Create comprehensive comparison table
    print("\nMethod Comparison Results:")
    comparison_data = [
        ["Metric", "GeoPandas", "KDTree"],
        ["Time (s)", f"{geopandas_perf['time']:.3f}", f"{kdtree_perf['time']:.3f}"],
        ["Memory (MB)", f"{geopandas_perf['memory']:.3f}", f"{kdtree_perf['memory']:.3f}"],
        ["Total Stations", geopandas_perf['count'], kdtree_perf['count']],
        ["Matching Stations", len(geopandas_ids.intersection(kdtree_ids)), len(geopandas_ids.intersection(kdtree_ids))],
        ["Unique Stations", len(geopandas_ids - kdtree_ids), len(kdtree_ids - geopandas_ids)]
    ]
    print(tabulate(comparison_data, headers='firstrow', tablefmt='psql', numalign='right'))

    # Use GeoPandas results for final output
    if kdtree_stations:
        print_fuel_station_table(
            kdtree_stations[:10],
            title=(f"\nFound {len(kdtree_stations)} fuel stations within "
                   f"{args.distance} miles of route. Showing first 10:")
        )


if __name__ == "__main__":
    main()
