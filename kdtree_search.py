# Third-party data handling and analysis
import numpy as np
from scipy.spatial import cKDTree
from scipy.interpolate import interp1d


def interpolate_route_points_scipy(route_points, max_distance=0.01):
    """Interpolate route points to ensure maximum distance between points.

    Args:
        route_points (list): List of dictionaries containing route points
        max_distance (float): Maximum distance between points in degrees

    Returns:
        list: Interpolated route points
    """
    # Extract coordinates
    coords = np.array([[p['lat'], p['lng']] for p in route_points])

    # Calculate cumulative distance along route
    diffs = np.diff(coords, axis=0)
    segment_lengths = np.sqrt(np.sum(diffs**2, axis=1))
    cum_distance = np.concatenate(([0], np.cumsum(segment_lengths)))

    # Create interpolation functions for lat and lon
    lat_interp = interp1d(cum_distance, coords[:, 0])
    lon_interp = interp1d(cum_distance, coords[:, 1])

    # Calculate number of points needed
    total_distance = cum_distance[-1]
    num_points = int(np.ceil(total_distance / max_distance)) + 1

    # Generate evenly spaced points
    distances = np.linspace(0, total_distance, num_points)

    # Interpolate new points
    new_points = [
        {'lat': lat_interp(d), 'lng': lon_interp(d)}
        for d in distances
    ]

    return new_points


def find_fuel_stations_kdtree(route_points, fuel_locations, distance_miles=1.0):
    """Find fuel stations within specified distance of route using optimized KDTree search

    Args:
        route_points (list): List of dictionaries containing route points
        fuel_locations (list): List of dictionaries containing fuel station data
        distance_miles (float): Search radius in miles (default: 1.0)

    Returns:
        list: Fuel stations within specified distance of route
    """
    # Convert distance to degrees (approximate)
    distance_degrees = distance_miles / 69.0  # 69 miles per degree of lat/lon

    # Convert fuel locations to numpy array for KDTree
    coords = np.array([[loc['lat'], loc['lon']] for loc in fuel_locations])

    # Create KDTree from coordinates
    tree = cKDTree(coords)

    # Interpolate route points using scipy method
    interpolated_points = interpolate_route_points_scipy(route_points, max_distance=distance_degrees/2)

    # Convert interpolated points to numpy array for vectorized operations
    route_coords = np.array([[p['lat'], p['lng']] for p in interpolated_points])

    # Use batch processing for query_ball_point
    batch_size = 1000  # Adjust based on memory constraints
    nearby_indices = set()

    for i in range(0, len(route_coords), batch_size):
        batch = route_coords[i:i + batch_size]
        batch_indices = tree.query_ball_point(batch, distance_degrees)
        nearby_indices.update(*batch_indices)

    # Convert indices to list of stations
    return [fuel_locations[i] for i in sorted(nearby_indices)]
