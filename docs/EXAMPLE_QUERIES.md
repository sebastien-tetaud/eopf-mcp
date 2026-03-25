# Example Data Queries

This document provides example questions you can ask the EOPF STAC Chat to query Earth Observation data based on metadata and location.

## Quick Start Examples (Tested & Verified)

These queries are tested to return metadata from the EOPF STAC catalog:

```
List all available collections
Find Sentinel-2 L2A data over Paris from March 2026
Search for Sentinel-2 L2A imagery covering Rome, Italy
What Sentinel-2 L2A data is available for Venice in 2026?
Get Sentinel-2 L2A data for Barcelona from this year
Find Sentinel-2 L2A imagery covering the Mediterranean coast
```

**Note**: These queries return metadata (dates, locations, item IDs). Visualization availability depends on whether items have been ingested into the Titiler service.

## Location-Based Queries

### By Geographic Area

**Europe:**
```
Show me Sentinel-2 L2A data over Rome, Italy from the last month
Find Sentinel-2 L2A images covering Paris, France from March 2026
What Sentinel-2 L2A data is available for the Alps region?
Get recent Sentinel-2 L2A imagery over Barcelona, Spain
```

**Bounding Box Queries:**
```
Search for Sentinel-2 L2A data in bbox [11.0, 44.0, 13.0, 46.0] from March 2026
Find Sentinel-2 L2A data between coordinates [10.5, 45.5, 12.5, 47.5] in 2026
Show me Sentinel-2 L2A data in the region bounded by [2.2, 48.8, 2.4, 48.9] from this year
```

**Specific Locations:**
```
What satellite imagery is available for Vienna, Austria?
Find Sentinel-2 scenes covering the Mediterranean Sea
Show me data for the Italian coastline near Venice
Get imagery for the Po Valley region in northern Italy
```

### By Country/Region

```
What Sentinel-2 collections cover Germany?
Find all available data for the Iberian Peninsula
Show me Sentinel-3 data over the North Sea
List available imagery for the Adriatic Sea region
```

## Time-Based Queries

### Recent Data

```
What is the latest Sentinel-2 data available?
Show me the most recent imagery from the last week
Find Sentinel-2 data from the past 30 days
Get the newest available Sentinel-3 scenes
```

### Specific Time Periods

```
Find Sentinel-2 data from January 2025
Show me imagery from summer 2024 (June-August)
What data is available from October 15-31, 2024?
Get Sentinel-2 scenes from the first quarter of 2025
List all data acquired in December 2024
```

### Date Ranges

```
Search for Sentinel-2 data between 2024-06-01 and 2024-08-31
Find imagery from January 1 to March 31, 2025
Show me data collected during spring 2024
What's available from the last 6 months?
```

## Combined Location + Time Queries

### City-Based

```
Find Sentinel-2 data over London from January 2025
Show me Paris imagery from the last 2 months
Get Munich satellite data from summer 2024
What Sentinel-2 scenes are available for Brussels in October 2024?
```

### Region + Season

```
Show me Mediterranean Sea data from summer 2024
Find Alpine region imagery from winter 2024-2025
Get coastal data for Spain from autumn 2024
Search for agricultural areas in France from spring 2024
```

### Specific Events/Monitoring

```
Find Sentinel-2 data over Venice during high water season (Nov-Dec 2024)
Show me imagery of agricultural areas in Tuscany during harvest season
Get coastal monitoring data for the Netherlands from storm season
Find snow cover data for the Alps from January-March 2025
```

## Metadata-Based Queries

### By Satellite/Collection

```
List all available Sentinel-2 L2A collections
What Sentinel-3 OLCI data is available?
Show me all Sentinel-2 collections
Compare Sentinel-2 and Sentinel-3 coverage
⚠️ Note: Sentinel-1 data can be queried but cannot be visualized
```

### By Data Properties

```
Find cloud-free Sentinel-2 data over Rome
Show me high-quality imagery with low cloud cover
Get Sentinel-2 data with complete coverage (no gaps)
Find the best quality scenes from the last month
```

### By Processing Level

```
What L2A (atmospherically corrected) Sentinel-2 data is available?
Show me all Level-2A products for my area of interest
Find processed Sentinel-2 Surface Reflectance data
```

## Visualization Queries

**Note**: The chatbot will only provide visualization instructions if you explicitly request it. For general queries, you'll receive metadata only.

### Map Display (Explicit Requests)

```
Show me Sentinel-2 data on a map for Rome, Italy
Visualize the latest imagery over Paris
Display Sentinel-2 true color composite for Barcelona
Can you show me false color infrared for vegetation monitoring?
Please visualize this data
```

### Band Combinations (Explicit Requests)

```
Show me true color RGB (bands B04, B03, B02) for this area
Display false color infrared (bands B08, B04, B03) for vegetation
Create a natural color visualization
Show me the NIR band for vegetation analysis
Visualize this with different band combinations
```

## Advanced Queries

### Multi-Criteria

```
Find cloud-free Sentinel-2 data over the Alps from January 2025
Show me recent high-quality imagery of coastal areas in Italy
Get Sentinel-2 L2A data for agricultural monitoring in France from June-August 2024
Find the best available scenes for the Po River delta from the last 3 months
```

### Data Discovery

```
What is the temporal coverage of Sentinel-2 data?
How many Sentinel-2 scenes are available for my region?
What is the spatial resolution of Sentinel-2 data?
Which bands are available in Sentinel-2 L2A products?
```

### Download/Access

```
How can I download this Sentinel-2 data?
Give me the Zarr URLs for the latest scene over Rome
Show me Python code to access this data with xarray
What are the available data formats?
```

## Bounding Box Format

When specifying bounding boxes, use the format: **[west, south, east, north]** in WGS84 coordinates.

**Example coordinates:**
- Rome, Italy: `[12.4, 41.8, 12.6, 42.0]`
- Paris, France: `[2.2, 48.8, 2.5, 49.0]`
- Barcelona, Spain: `[2.1, 41.3, 2.2, 41.5]`
- Alps region: `[6.0, 45.0, 13.0, 48.0]`
- Venice, Italy: `[12.2, 45.3, 12.5, 45.6]`

## Important Notes

### Visualization Limitations

⚠️ **Visualization is very limited - most items are NOT available**
- **Sentinel-2 L2A**: ✅ Technically supports visualization, but **very few items are ingested in Titiler**
- **Sentinel-1**: ❌ SAR data cannot be visualized
- **Sentinel-3**: ❌ Cannot be visualized with Titiler
- **IMPORTANT**: The vast majority of items in the STAC catalog (including recent 2024-2026 data) are **NOT available for visualization**
- The Titiler service only contains a small subset of processed items
- You can always query metadata and access raw Zarr data, but map visualization may not work

### Available Collections

The EOPF STAC catalog includes:
- **Sentinel-2 L2A**: Surface Reflectance (10-60m resolution) - ✅ Visualization supported
- **Sentinel-3 OLCI**: Ocean and Land Color Instrument - ❌ Visualization not supported
- **Sentinel-1**: SAR data - ❌ Visualization not supported

### Data Access

- All STAC metadata is publicly accessible (no authentication required)
- Zarr data available via HTTPS (no credentials needed)
- S3 access requires credentials (optional, for advanced use)

## Tips for Better Queries

1. **Be specific about location**: Use city names, regions, or bounding boxes
2. **Specify time ranges**: Use date ranges or relative terms (last month, summer 2024)
3. **Mention collection**: Specify Sentinel-2, Sentinel-3, or collection ID
4. **Clarify your goal**:
   - For metadata only: "Find", "Search", "List", "What data is available"
   - For visualization: "Show on map", "Visualize", "Display"
   - For download: "How do I download", "Give me access code", "How to use this data"
5. **Use natural language**: The chatbot understands conversational queries
6. **Visualization is opt-in**: The chatbot won't suggest visualization unless you explicitly ask for it

## Example Workflow

```
User: "Find Sentinel-2 data over Rome from the last 2 weeks"
→ Chat returns: List of available scenes with dates and metadata

User: "Show me the latest scene on a map"
→ Chat displays: Interactive map with the Sentinel-2 imagery

User: "Can you give me the download link for this data?"
→ Chat provides: Zarr URLs and Python code for data access
```

## Getting Help

If you're unsure what to ask:
- "What data is available?"
- "List all collections"
- "Show me example queries"
- "What can you help me with?"

The chatbot uses MCP (Model Context Protocol) to query the EOPF STAC catalog and can help with:
- Data discovery and search
- Metadata exploration
- Map visualization (Sentinel-2/3)
- Data access instructions
- Python code generation for data analysis
