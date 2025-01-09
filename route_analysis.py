from math import radians, sin, cos, sqrt, atan2
import numpy as np
from tabulate import tabulate
from shapely.geometry import LineString
from googlemaps.convert import decode_polyline


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c * 1000  # Convert to meters


def analyze_route_spacing(route_points, print_analysis=True):
    """Analyze spacing between route points

    Args:
        route_points (list): List of route points
        print_analysis (bool): Whether to print the analysis table (default: True)
    """
    distances = []
    for i in range(len(route_points)-1):
        point1 = route_points[i]
        point2 = route_points[i+1]
        dist = calculate_distance(point1['lat'], point1['lng'], point2['lat'], point2['lng'])
        distances.append(dist)
    total_distance = sum(distances)

    analysis = {
        'Total Points': len(route_points),
        'Avg Distance (m)': round(np.mean(distances), 2),
        'Min Distance (m)': round(min(distances), 2),
        'Max Distance (m)': round(max(distances), 2),
        'Std Dev (m)': round(np.std(distances), 2),
        'Total Distance (km)': round(total_distance / 1000, 2),
        'Total Distance (mi)': round(total_distance / 1609.34, 2),
    }

    if print_analysis:
        print("\nRoute Analysis:")
        table_data = [[key, value] for key, value in analysis.items()]
        print(tabulate(table_data, headers=['Metric', 'Value'], tablefmt='psql', numalign='decimal', floatfmt='.2f'))

    return analysis


def get_route_points(gmaps_client, origin, destination, detailed=False, simplify_tolerance=0.0002):
    """Get route points from Google Maps API

    Args:
        gmaps_client: Initialized Google Maps client
        origin (str): Starting address
        destination (str): Ending address
        detailed (bool): If True, returns detailed route. If False, returns simplified overview route.
        simplify_tolerance (float): Tolerance for route simplification (in degrees). Higher values = fewer points. 
                                Default 0.0002 (~22m). Default can reduce number of points by > 10x while preserving
                                route shape while still being accurate to within 22m.

    Returns:
        list: Route points, each containing:
            - lat: Latitude coordinate
            - lng: Longitude coordinate
    """
    directions = gmaps_client.directions(origin, destination)

    if not detailed:
        # Return simplified overview route
        polyline = directions[0]['overview_polyline']['points']
        return decode_polyline(polyline)

    # Get detailed route with precise route points
    all_points = []
    for leg in directions[0]['legs']:
        for step in leg['steps']:
            step_points = decode_polyline(step['polyline']['points'])
            all_points.extend(step_points)

    if simplify_tolerance:
        original_count = len(all_points)

        # Convert points to LineString
        coords = [(p['lng'], p['lat']) for p in all_points]
        line = LineString(coords)

        print(f"\nSimplifying route from {original_count} points...")
        print(f"Using tolerance of {simplify_tolerance} degrees (≈{simplify_tolerance * 111000:.0f}m)")
        print("This means any point that deviates less than this distance from the simplified ")
        print("route will be removed while preserving the overall route shape.")

        # Simplify the line
        simplified = line.simplify(tolerance=simplify_tolerance, preserve_topology=True)

        # Convert back to points format
        simplified_points = [{'lat': y, 'lng': x} for x, y in simplified.coords]

        print(f"Route simplified to {len(simplified_points)} points")
        print(f"Reduction: {(1 - len(simplified_points)/original_count)*100:.1f}%")

        return simplified_points

    return all_points


def validate_address(gmaps_client, location):
    """Validate a location using Google Maps Geocoding API.

    Args:
        gmaps_client: Initialized Google Maps client
        location (str): Address string or lat,lon pair (e.g. "40.7128,-74.0060")

    Returns:
        str or None: Formatted address if valid, None if invalid
    """
    try:
        # Check if input might be lat,lon
        if ',' in location and all(part.replace('.', '').replace('-', '').isdigit()
                                   for part in location.split(',')):
            lat, lon = map(float, location.split(','))

            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                print(f"Invalid location '{location}': Invalid coordinate ranges")
                return None

            # Reverse geocode to verify location exists
            result = gmaps_client.reverse_geocode((lat, lon))

        else:
            # Geocode address string
            result = gmaps_client.geocode(location)

        if not result:
            print(f"Invalid location '{location}': Location not found")
            return None

        formatted_address = result[0]['formatted_address']
        print(f"Validated location: {formatted_address}")
        return formatted_address

    except Exception as e:
        print(f"Invalid location '{location}': Validation error: {str(e)}")
        return None
