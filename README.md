# KodeLabz Toolkit for Blender

![Blender Version](https://img.shields.io/badge/Blender-3.0%2B-orange)
![License](https://img.shields.io/badge/License-Proprietary-blue)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)

A modular, expandable Blender add-on that combines the most in-demand tools and workflows under one clean, branded UI. Think of it like Blender's Swiss Army knife for professionals and studios.

## Features

The KodeLabz Toolkit includes several powerful modules:

### AI Texture Lab
- Text-to-texture generation with Replicate API
- Seamless tiling options
- PBR material creation
- Advanced settings for fine-tuning

### AutoMesh Pro
- Retopology with multiple methods (Voxel, Quad, Decimate)
- Mesh cleanup tools
- UV unwrapping with various projection methods
- 3D print preparation

### ScatterCraft
- Asset scatter system for environments and scenes
- Surface, volume, and path-based distribution
- Randomization of scale, rotation, and placement
- Overlap avoidance

## Installation

### From GitHub Release (Recommended)
1. Go to the [Releases](../../releases) page
2. Download the latest version ZIP file
3. In Blender, go to Edit > Preferences > Add-ons
4. Click "Install..." and select the downloaded ZIP file
5. Enable the "KodeLabz Toolkit" add-on

### From Source
1. Clone this repository
2. Run `python package_addon.py` to create the add-on ZIP
3. Follow steps 3-5 above to install the ZIP file

## Requirements
- Blender 3.0 or newer
- Internet connection for AI Texture Lab features
- Python `requests` module (for API calls)

To install the required Python modules:
```
<blender_path>/python/bin/python -m pip install requests
```

## Usage

After installation, the KodeLabz Toolkit can be found in the 3D View sidebar. Look for the "KodeLabz" tab.

### API Setup
For AI Texture Lab, you need to set up your Replicate API token:
1. Go to Edit > Preferences > Add-ons
2. Find "KodeLabz Toolkit" and expand it
3. Enter your API token in the settings

## Modules

### AI Texture Lab
Generate PBR textures from text prompts using AI:
1. Enter a text description
2. Select material type
3. Adjust settings as needed
4. Click "Generate Texture"

### AutoMesh Pro
Optimize and prepare 3D models:
1. Select a mesh object
2. Choose retopology, cleanup, UV unwrap, or 3D print prep
3. Adjust settings for the selected operation
4. Click the corresponding "Apply" button

### ScatterCraft
Distribute objects across surfaces or volumes:
1. Select a scatter method (Surface, Volume, Path)
2. Add objects to scatter
3. Adjust density, scale, and rotation settings
4. Click "Execute Scatter"

## Development

### Setup
1. Clone the repository
2. Make your changes
3. Use `python package_addon.py` to test the add-on

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
 2025 KodeLabz - All Rights Reserved

## Contact
For support or feature requests, contact KodeLabz at support@kodelabz.com
