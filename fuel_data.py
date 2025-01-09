import pymongo
from tabulate import tabulate


def connect_to_mongodb(db_url, db_name):
    """Establish MongoDB connection

    Args:
        db_url (str): MongoDB connection URL
        db_name (str): Name of the database

    Returns:
        pymongo.database.Database: MongoDB database connection
    """
    client = pymongo.MongoClient(db_url)
    return client[db_name]


def get_fuel_locations(db):
    """Query MongoDB for Loves/Pilot fuel locations"""
    fuel_locations = db.fuelLocations.find(
        {
            "fuelStationCompanyName": {
                "$in": ["Loves", "Pilot"]
            }
        },
        {
            "address": 1,
            "city": 1,
            "lat": 1,
            "lon": 1,
            "locationId": 1,
            "state": 1,
            "zipCode": 1,
            "_id": 1  # Include the MongoDB _id field
        }
    )
    return list(fuel_locations)


def get_retail_fuel_prices(db):
    """Query MongoDB for retail fuel prices."""
    fuel_prices = db.fuelPrices.find(
        {},
        {
            "location_id": 1,
            "dieselPrice": 1,
            "_id": 0
        }
    )
    return list(fuel_prices)


def merge_fuel_data(fuel_locations, fuel_prices):
    """Merge fuel locations with their corresponding prices"""
    # Create price lookup dictionary using MongoDB _id
    price_lookup = {str(price['location_id']): price['dieselPrice']
                    for price in fuel_prices}

    # Merge data
    merged_locations = []
    for location in fuel_locations:
        location_data = {
            'locationId': location['locationId'],
            'lat': location['lat'],
            'lon': location['lon'],
            'address': f"{location['address']}, {location['city']}, {location['state']} {location['zipCode']}",
            'dieselPrice': price_lookup.get(str(location['_id']), 'N/A')  # Use MongoDB _id for lookup
        }
        merged_locations.append(location_data)

    return merged_locations


def validate_fuel_locations(formatted_locations):
    """Validate coordinates of formatted fuel locations and separate valid from invalid entries."""
    valid_locations = []
    invalid_locations = []

    for location in formatted_locations:
        try:
            lat = float(location['lat'])
            lon = float(location['lon'])
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                invalid_locations.append(location)
                continue
            valid_locations.append(location)
        except (ValueError, TypeError, KeyError):
            invalid_locations.append(location)
            continue

    # Print validation results
    print("\nFuel Location Validation Results:")
    print(f"Total locations: {len(valid_locations) + len(invalid_locations)}")
    print(f"Valid locations: {len(valid_locations)}")
    print(f"Invalid locations: {len(invalid_locations)}")

    if invalid_locations:
        print("\nInvalid Location Details:")
        invalid_data = [
            ["Location ID", "Address", "Lat", "Lon"],
            *[[loc['locationId'], loc['address'], loc['lat'], loc['lon']]
                for loc in invalid_locations]
        ]
        print(tabulate(invalid_data, headers='firstrow', tablefmt='psql'))

    return valid_locations, invalid_locations


def get_fuel_locations_with_prices(db_url, db_name):
    """Get all valid fuel locations with prices from the database.

    Args:
        db_url (str): MongoDB connection URL
        db_name (str): Name of the database

    Returns:
        list: Valid fuel locations with merged price data
    """
    # Connect to database
    db = connect_to_mongodb(db_url, db_name)

    # Get raw data from database
    fuel_locations = get_fuel_locations(db)
    fuel_prices = get_retail_fuel_prices(db)

    # Merge and validate data
    merged_locations = merge_fuel_data(fuel_locations, fuel_prices)
    valid_locations, _ = validate_fuel_locations(merged_locations)

    return valid_locations
