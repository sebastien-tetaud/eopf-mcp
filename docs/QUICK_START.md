# Quick Start: Download Zarr Data in 3 Steps

## Step 1: Start Gradio
```bash
uv run python gradio_app.py
```
Open: http://localhost:7860

## Step 2: Ask for Zarr URLs
In the Gradio chat:
```
Get Zarr URLs for Sentinel-2 L1C over bbox [11.2, 45.5, 11.3, 45.6] from January 2024
```

Claude returns URLs like:
```
s3://eodata/Sentinel-2/.../IMG_DATA.zarr
```

## Step 3: Download

### Option A: Ask Claude for Instructions
```
How do I download the first Zarr file?
```

Claude provides ready-to-run code with your credentials!

### Option B: Use Download Script
```bash
uv run python download_zarr.py "s3://eodata/.../IMG_DATA.zarr"
```

### Option C: Direct Python
```python
import xarray as xr
import s3fs
import os
from dotenv import load_dotenv

load_dotenv()

s3 = s3fs.S3FileSystem(
    key=os.getenv("ACCESS_KEY_ID"),
    secret=os.getenv("SECRET_ACCESS_KEY"),
    client_kwargs={'endpoint_url': 'https://eodata.dataspace.copernicus.eu'}
)

store = s3fs.S3Map(root='s3://eodata/.../IMG_DATA.zarr', s3=s3)
ds = xr.open_zarr(store)
print(ds)
```

## Your Credentials (Already Configured)
✅ Loaded from `.env`:
- ACCESS_KEY_ID=S70BXHVHY3HGPLBAA228
- SECRET_ACCESS_KEY=hUBy...

## Example Workflow
```
# In Gradio chat:
You: Find Sentinel-2 data over Northern Italy
Claude: [Shows results]

You: Get Zarr URLs
Claude: s3://eodata/.../data1.zarr, s3://eodata/.../data2.zarr

You: How to download the first one?
Claude: [Provides Python code]

# Copy code and run locally or use:
$ uv run python download_zarr.py "s3://eodata/.../data1.zarr"
💾 Download to local file? (y/n): y
✅ Downloaded to: ./data/data1.zarr
```

## Next Steps
- 📖 Read [DOWNLOAD_GUIDE.md](DOWNLOAD_GUIDE.md) for complete instructions
- 🔧 See [USAGE_GUIDE.md](USAGE_GUIDE.md) for all MCP features
- 💡 Check [README.md](README.md) for tool documentation
