# ND Estates Property Database

This document describes the property database system that enhances Google Analytics reporting by providing accurate URL-to-campaign mappings based on real property data.

## Overview

The property database stores current property listings from the ND Estates XML feed (`https://api.ndestates.com/feeds/ndefeed.xml`) and automatically assigns campaigns based on property attributes like parish and property type.

## Database Structure

The SQLite database (`data/properties.db`) contains a `properties` table with the following fields:

- `reference`: Unique property reference number
- `url`: Full property listing URL
- `property_name`: Property title/name
- `house_name`: House name (if applicable)
- `property_type`: Type (Apartment, House, etc.)
- `price`: Property price
- `parish`: Jersey parish location
- `status`: Availability status
- `type`: Sale type (buy/rent)
- `bedrooms`, `bathrooms`, `receptions`, `parking`: Property details
- `latitude`, `longitude`: Geographic coordinates
- `description`: Property description
- `image_one` to `image_five`: Property images
- `campaign`: Automatically assigned campaign name
- `last_updated`, `created_at`: Timestamps

## Campaign Assignment Logic

Campaigns are automatically assigned based on property attributes:

### Parish-Based Campaigns
- **St Helier Properties/Apartments**: Properties in St Helier
- **St Clement Properties/Apartments**: Properties in St Clement
- **St Saviour Properties/Apartments**: Properties in St Saviour
- **St Peter Properties/Apartments**: Properties in St Peter
- **St Martin Properties/Apartments**: Properties in St Martin
- **St Ouen Properties/Apartments**: Properties in St Ouen
- **St John Properties/Apartments**: Properties in St John
- **St Brelade Properties/Apartments**: Properties in St Brelade
- **Trinity Properties/Apartments**: Properties in Trinity
- **Grouville Properties/Apartments**: Properties in Grouville

### Property Type Differentiation
- **Properties**: Houses and other non-apartment property types
- **Apartments**: Specifically apartment/flat properties

## Setup Instructions

### Initial Setup
Run the setup script to create the database and import initial data:

```bash
python3 scripts/setup_property_database.py
```

This will:
1. Create the SQLite database with proper schema
2. Fetch current property data from the XML feed
3. Assign campaigns to all properties
4. Set up indexes for fast lookups

### Updating Property Data
To refresh the database with the latest property listings:

```bash
python3 scripts/import_property_feed.py
```

This will:
- Fetch the latest XML feed
- Update existing properties
- Add new properties
- Reassign campaigns as needed

## Integration with Analytics Reports

The source reports (`scripts/all_pages_sources_report.py`) now automatically:

1. **Load campaign mappings** from the database instead of static JSON
2. **Match URLs** to their corresponding campaigns
3. **Include campaign data** in CSV exports and PDF reports
4. **Provide fallback mappings** for URLs not in the database

### Report Output
- **Console output**: Shows campaign for each page
- **CSV files**: Include "Campaign" column with assigned campaigns
- **PDF reports**: Display campaign information in tables
- **Summary reports**: Group data by campaign assignments

## Files Overview

- `scripts/create_property_database.py`: Database schema creation
- `scripts/import_property_feed.py`: XML feed import and processing
- `scripts/setup_property_database.py`: Complete setup script
- `data/properties.db`: SQLite database file
- `config/url_campaign_mapping.json`: Source unification rules only

## Benefits

1. **Accurate Campaign Mapping**: URLs are mapped to specific campaigns based on real property data
2. **Automatic Updates**: Campaign assignments update when property data changes
3. **Granular Reporting**: Analytics reports can now segment by parish and property type
4. **Scalable**: Easy to add new campaign assignment rules
5. **Real-time Data**: Property database stays current with the XML feed

## Troubleshooting

### Database Not Found
If reports show "Property database not found", run:
```bash
python3 scripts/setup_property_database.py
```

### Outdated Data
If property listings seem outdated, refresh with:
```bash
python3 scripts/import_property_feed.py
```

### Campaign Assignment Issues
Campaigns are assigned based on the `get_property_campaign()` function in `create_property_database.py`. Modify this function to change assignment logic.

## Future Enhancements

- Add price-based campaign segmentation
- Include property status (available/sold) in campaign logic
- Add geographic clustering for broader campaign groups
- Implement property search functionality
- Add data validation and cleanup routines