#!/usr/bin/env python3
"""
EOPF STAC MCP Server

An MCP server that provides tools to interact with the EOPF STAC catalog
for retrieving Earth Observation metadata.

AUTHENTICATION NOTES:
- STAC Catalog: Publicly accessible, NO credentials required for querying
- S3 Zarr Data: Requires ACCESS_KEY_ID and SECRET_ACCESS_KEY for downloads
  (only needed for download_zarr_info tool with S3 URLs)
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any

import pystac_client
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables
load_dotenv()

# STAC catalog configuration
STAC_URL = os.getenv("STAC_URL", "https://stac.core.eopf.eodc.eu")

# Initialize the MCP server
app = Server("eopf-stac-server")

# Cache the STAC catalog connection to avoid reconnecting on every tool call
_catalog_cache = None


def sanitize_error_message(error: Exception) -> str:
    """Remove potential secrets from error messages."""
    error_str = str(error)

    # Redact common secret patterns
    error_str = re.sub(r'sk-ant-[a-zA-Z0-9-]+', 'sk-ant-***REDACTED***', error_str)
    error_str = re.sub(r'Bearer [a-zA-Z0-9._-]+', 'Bearer ***REDACTED***', error_str)
    error_str = re.sub(r'api[_-]?key["\s:=]+[a-zA-Z0-9-]+', 'api_key=***REDACTED***', error_str, flags=re.IGNORECASE)
    error_str = re.sub(r'token["\s:=]+[a-zA-Z0-9._-]+', 'token=***REDACTED***', error_str, flags=re.IGNORECASE)
    error_str = re.sub(r'secret["\s:=]+[a-zA-Z0-9]+', 'secret=***REDACTED***', error_str, flags=re.IGNORECASE)

    return error_str


def get_catalog():
    """
    Get cached STAC catalog connection.

    Note: The EOPF STAC catalog is publicly accessible and does not require authentication.
    The connection is cached to avoid reconnecting on every tool call.
    """
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = pystac_client.Client.open(STAC_URL)
    return _catalog_cache


def get_s3_credentials():
    """
    Get S3 credentials from environment for Zarr data downloads.

    Note: Credentials are only needed for downloading Zarr data from S3,
    not for querying the STAC catalog itself.
    """
    return {
        "key": os.getenv("ACCESS_KEY_ID"),
        "secret": os.getenv("SECRET_ACCESS_KEY"),
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for STAC catalog interaction."""
    return [
        Tool(
            name="list_collections",
            description="List all available collections in the EOPF STAC catalog",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_collection",
            description="Get detailed information about a specific collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection_id": {
                        "type": "string",
                        "description": "The ID of the collection to retrieve",
                    },
                },
                "required": ["collection_id"],
            },
        ),
        Tool(
            name="search_items",
            description="Search for items in the STAC catalog with optional filters. Returns item metadata. Only provide visualization instructions if the user explicitly asks to visualize or show on a map. IMPORTANT: Only Sentinel-2 L2A products support visualization. Sentinel-1 and Sentinel-3 products cannot be visualized.",
            inputSchema={
                "type": "object",
                "properties": {
                    "collections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of collection IDs to search in (e.g., 'sentinel-2-l2a', 'sentinel-3-olci-l2-wfr').",
                    },
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Bounding box [west, south, east, north] in WGS84",
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "datetime": {
                        "type": "string",
                        "description": "Datetime range (e.g., '2023-01-01/2023-12-31' or single date)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of items to return (default: 10)",
                        "default": 10,
                    },
                    "query": {
                        "type": "object",
                        "description": "Additional query parameters",
                    },
                    "include_zarr": {
                        "type": "boolean",
                        "description": "Include Zarr asset URLs in results (default: true)",
                        "default": True,
                    },
                },
            },
        ),
        Tool(
            name="get_item",
            description="Get detailed information about a specific STAC item",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection_id": {
                        "type": "string",
                        "description": "The collection ID containing the item",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the item to retrieve",
                    },
                },
                "required": ["collection_id", "item_id"],
            },
        ),
        Tool(
            name="get_item_assets",
            description="Get the assets (data files) available for a specific item",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection_id": {
                        "type": "string",
                        "description": "The collection ID containing the item",
                    },
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the item",
                    },
                },
                "required": ["collection_id", "item_id"],
            },
        ),
        Tool(
            name="get_zarr_urls",
            description="DEPRECATED: Use search_items with include_zarr=true instead. Get Zarr file URLs for items matching a search query. Returns direct access URLs to Zarr datasets. IMPORTANT: Only Sentinel-2 L2A products support visualization. Sentinel-1, Sentinel-3, and Sentinel-2 L1C products cannot be visualized.",
            inputSchema={
                "type": "object",
                "properties": {
                    "collections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of collection IDs to search in (Note: Sentinel-1 data cannot be visualized)",
                    },
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Bounding box [west, south, east, north] in WGS84",
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "datetime": {
                        "type": "string",
                        "description": "Datetime range (e.g., '2023-01-01/2023-12-31')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of items to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="download_zarr_info",
            description="Get access information for a Zarr dataset URL. Returns the URL type (HTTPS/S3) and access method. ONLY call this tool if the user explicitly asks for download information, access code, or how to use the data. Do not call this tool for general search queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "zarr_url": {
                        "type": "string",
                        "description": "The Zarr URL to access (HTTPS or S3 URL from search results)",
                    },
                    "include_code": {
                        "type": "boolean",
                        "description": "Include Python code examples (default: false, only include if user explicitly asks for code/script)",
                        "default": False,
                    },
                },
                "required": ["zarr_url"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for STAC catalog operations."""

    try:
        catalog = get_catalog()

        if name == "list_collections":
            collections = list(catalog.get_collections())
            collections_list = []
            for col in collections:
                col_dict = {
                    "id": col.id,
                    "title": col.title or col.id,
                    "description": col.description,
                    "license": col.license,
                    "extent": {
                        "spatial": col.extent.spatial.bboxes if col.extent and col.extent.spatial else None,
                        "temporal": [
                            [str(interval[0]), str(interval[1])]
                            for interval in (col.extent.temporal.intervals if col.extent and col.extent.temporal else [])
                        ],
                    },
                }

                # Add visualization support flag
                # Only Sentinel-2 L2A products support visualization
                if "sentinel-2" in col.id.lower() and "l2a" in col.id.lower():
                    col_dict["visualization_supported"] = True
                    col_dict["visualization_note"] = "Sentinel-2 L2A supports visualization with Titiler, but only a small subset of items are currently ingested"
                else:
                    col_dict["visualization_supported"] = False
                    if "sentinel-1" in col.id.lower():
                        col_dict["visualization_note"] = "Sentinel-1 SAR data cannot be visualized with Titiler"
                    elif "sentinel-3" in col.id.lower():
                        col_dict["visualization_note"] = "Sentinel-3 data cannot be visualized with Titiler"
                    else:
                        col_dict["visualization_note"] = "Visualization not supported for this collection"

                collections_list.append(col_dict)

            result = {
                "total": len(collections),
                "collections": collections_list,
                "note": "Only Sentinel-2 L2A products support visualization in map interfaces, but very few items are available in Titiler. Sentinel-1 and Sentinel-3 products cannot be visualized. Most queries should focus on metadata retrieval rather than visualization.",
            }
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "get_collection":
            collection_id = arguments["collection_id"]
            collection = catalog.get_collection(collection_id)

            result = {
                "id": collection.id,
                "title": collection.title,
                "description": collection.description,
                "license": collection.license,
                "keywords": collection.keywords,
                "providers": [
                    {
                        "name": p.name,
                        "roles": p.roles,
                        "url": p.url,
                    }
                    for p in (collection.providers or [])
                ],
                "extent": {
                    "spatial": collection.extent.spatial.bboxes if collection.extent and collection.extent.spatial else None,
                    "temporal": [
                        [str(interval[0]), str(interval[1])]
                        for interval in (collection.extent.temporal.intervals if collection.extent and collection.extent.temporal else [])
                    ],
                },
                "summaries": collection.summaries.to_dict() if collection.summaries else {},
            }
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "search_items":
            search_params = {}

            if "collections" in arguments:
                search_params["collections"] = arguments["collections"]
            if "bbox" in arguments:
                search_params["bbox"] = arguments["bbox"]
            if "datetime" in arguments:
                search_params["datetime"] = arguments["datetime"]
            if "query" in arguments:
                search_params["query"] = arguments["query"]

            limit = arguments.get("limit", 10)
            include_zarr = arguments.get("include_zarr", True)

            search = catalog.search(**search_params, max_items=limit)
            items = list(search.items())

            items_data = []
            for item in items:
                item_dict = {
                    "id": item.id,
                    "collection": item.collection_id,
                    "datetime": str(item.datetime) if item.datetime else None,
                    "geometry": item.geometry,
                    "bbox": item.bbox,
                    "properties": item.properties,
                    "assets": list(item.assets.keys()),
                }

                # Include Zarr URLs if requested
                if include_zarr:
                    zarr_assets = {}
                    for key, asset in item.assets.items():
                        # Look for Zarr files (check media type or file extension)
                        if (asset.media_type and "zarr" in asset.media_type.lower()) or \
                           (asset.href and ".zarr" in asset.href.lower()):
                            zarr_assets[key] = {
                                "url": asset.href,
                                "type": asset.media_type,
                                "roles": asset.roles,
                                "title": asset.title,
                            }

                    if zarr_assets:
                        item_dict["zarr_assets"] = zarr_assets

                items_data.append(item_dict)

            result = {
                "found": len(items),
                "items": items_data,
            }

            # Add warning if non-L2A data is detected
            collections = arguments.get("collections", [])
            has_non_l2a = any(
                not ("sentinel-2" in str(col).lower() and "l2a" in str(col).lower())
                for col in collections
            )
            if has_non_l2a and collections:
                result["visualization_warning"] = "⚠️ IMPORTANT: Only Sentinel-2 L2A products support visualization in map interfaces. Sentinel-1, Sentinel-3, and Sentinel-2 L1C products cannot be visualized with Titiler."

            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "get_item":
            collection_id = arguments["collection_id"]
            item_id = arguments["item_id"]

            collection = catalog.get_collection(collection_id)
            item = collection.get_item(item_id)

            result = {
                "id": item.id,
                "collection": item.collection_id,
                "datetime": str(item.datetime) if item.datetime else None,
                "geometry": item.geometry,
                "bbox": item.bbox,
                "properties": item.properties,
                "assets": {
                    key: {
                        "href": asset.href,
                        "type": asset.media_type,
                        "roles": asset.roles,
                        "title": asset.title,
                    }
                    for key, asset in item.assets.items()
                },
                "links": [
                    {"rel": link.rel, "href": link.href, "type": link.media_type}
                    for link in item.links
                ],
            }
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "get_item_assets":
            collection_id = arguments["collection_id"]
            item_id = arguments["item_id"]

            collection = catalog.get_collection(collection_id)
            item = collection.get_item(item_id)

            result = {
                "item_id": item.id,
                "collection": item.collection_id,
                "assets": {
                    key: {
                        "href": asset.href,
                        "type": asset.media_type,
                        "roles": asset.roles,
                        "title": asset.title,
                        "description": asset.description,
                    }
                    for key, asset in item.assets.items()
                },
            }
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "get_zarr_urls":
            search_params = {}

            if "collections" in arguments:
                search_params["collections"] = arguments["collections"]
            if "bbox" in arguments:
                search_params["bbox"] = arguments["bbox"]
            if "datetime" in arguments:
                search_params["datetime"] = arguments["datetime"]

            limit = arguments.get("limit", 10)

            search = catalog.search(**search_params, max_items=limit)
            items = list(search.items())

            zarr_data = []
            for item in items:
                # Find Zarr assets
                zarr_assets = {}
                for key, asset in item.assets.items():
                    # Look for Zarr files (check media type or file extension)
                    if (asset.media_type and "zarr" in asset.media_type.lower()) or \
                       (asset.href and ".zarr" in asset.href.lower()):
                        zarr_assets[key] = {
                            "url": asset.href,
                            "type": asset.media_type,
                            "roles": asset.roles,
                            "title": asset.title,
                        }

                if zarr_assets:
                    zarr_data.append({
                        "item_id": item.id,
                        "collection": item.collection_id,
                        "datetime": str(item.datetime) if item.datetime else None,
                        "bbox": item.bbox,
                        "zarr_assets": zarr_assets,
                    })

            result = {
                "found": len(zarr_data),
                "items": zarr_data,
            }

            # Add warning if non-L2A data is detected
            collections = arguments.get("collections", [])
            has_non_l2a = any(
                not ("sentinel-2" in str(col).lower() and "l2a" in str(col).lower())
                for col in collections
            )
            if has_non_l2a and collections:
                result["visualization_warning"] = "⚠️ IMPORTANT: Only Sentinel-2 L2A products support visualization in map interfaces. Sentinel-1, Sentinel-3, and Sentinel-2 L1C products cannot be visualized with Titiler."

            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "download_zarr_info":
            zarr_url = arguments["zarr_url"]
            include_code = arguments.get("include_code", False)

            # Get credentials
            creds = get_s3_credentials()
            has_creds = creds["key"] and creds["secret"]

            # Parse URL type
            is_s3 = zarr_url.startswith("s3://")
            is_https = zarr_url.startswith("https://")

            # Build basic result
            result = {
                "zarr_url": zarr_url,
                "url_type": "HTTPS" if is_https else "S3",
            }

            # For EOPF STAC Zarr URLs (HTTPS)
            if is_https:
                result["access_method"] = "Direct HTTPS access (no credentials needed)"
                result["note"] = "EOPF Zarr datasets are publicly accessible via HTTPS. No S3 credentials needed!"

                # Only include code if requested
                if include_code:
                    result["python_example"] = f"""# Open EOPF Zarr dataset directly via HTTPS
import xarray as xr

zarr_url = "{zarr_url}"
ds = xr.open_datatree(zarr_url, engine="zarr")
print(ds)"""
            else:
                # For S3 URLs
                result["access_method"] = "S3 access (requires credentials)"
                result["credentials_configured"] = has_creds
                result["credential_status"] = "✅ Credentials available" if has_creds else "⚠️ Credentials needed (ACCESS_KEY_ID and SECRET_ACCESS_KEY)"

                # Only include code if requested
                if include_code:
                    result["python_example"] = f"""# Using xarray with S3 credentials
import xarray as xr
import s3fs
import os
from dotenv import load_dotenv

load_dotenv()

s3 = s3fs.S3FileSystem(
    key=os.getenv('ACCESS_KEY_ID'),
    secret=os.getenv('SECRET_ACCESS_KEY'),
    client_kwargs={{'endpoint_url': 'https://eodata.dataspace.copernicus.eu'}}
)

store = s3fs.S3Map(root='{zarr_url}', s3=s3, check=False)
ds = xr.open_zarr(store)
print(ds)"""

            return [TextContent(type="text", text=json.dumps(result))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        safe_message = sanitize_error_message(e)
        return [TextContent(type="text", text=f"Error: {safe_message}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
