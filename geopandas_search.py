# Third-party data handling and analysis
import geopandas as gpd
from shapely.geometry import Point, LineString


def find_fuel_stations_geopandas(route_points, fuel_locations, distance_miles=1.0):
    """Find fuel stations within specified distance of route using GeoPandas

    Args:
        route_points (list): List of dictionaries containing route points with 'lat' and 'lng' keys
        fuel_locations (list): List of dictionaries containing fuel station data
        distance_miles (float): Search radius in miles (default: 1.0)

    Returns:
        list: Fuel stations within specified distance of route
    """
    # Convert route points to LineString
    route_coords = [(point['lng'], point['lat']) for point in route_points]
    route_line = LineString(route_coords)

    # Create GeoDataFrame for route
    route_gdf = gpd.GeoDataFrame(geometry=[route_line], crs="EPSG:4326")

    # Create GeoDataFrame for fuel stations
    fuel_points = [Point(loc['lon'], loc['lat']) for loc in fuel_locations]
    fuel_gdf = gpd.GeoDataFrame(
        fuel_locations,  # Pass the complete location data including diesel prices
        geometry=fuel_points,
        crs="EPSG:4326"
    )

    # Project to a local UTM coordinate system for accurate distance measurement
    # Get UTM zone from center of route
    center_lon = route_line.centroid.x
    utm_zone = int((center_lon + 180) / 6) + 1
    utm_crs = f"+proj=utm +zone={utm_zone} +datum=WGS84"

    # Project both GeoDataFrames to UTM
    route_gdf_utm = route_gdf.to_crs(utm_crs)
    fuel_gdf_utm = fuel_gdf.to_crs(utm_crs)

    # Create buffer around route (distance in meters)
    buffer_distance = distance_miles * 1609.34  # Convert miles to meters
    route_buffer = route_gdf_utm.geometry.buffer(buffer_distance)

    # Find stations within buffer
    nearby_stations = fuel_gdf_utm[fuel_gdf_utm.intersects(route_buffer.iloc[0])]

    # Convert back to original CRS and return as list of dictionaries
    nearby_stations = nearby_stations.to_crs("EPSG:4326")
    return nearby_stations[['locationId', 'lat', 'lon', 'address', 'dieselPrice']].to_dict('records')
