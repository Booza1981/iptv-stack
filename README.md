# IPTV Channel Logo Updater

This tool updates channel logos in IPTV/EPG XML files by matching channel names to logo files and applying specific fixes for problematic channels.

## Features

- Automatically matches channel names to logo files using a comprehensive database
- Applies specific fixes for channels that need manual attention
- Generates detailed reports of matched and unmatched channels
- Configurable via command-line arguments or by editing the script

## Directory Structure

```
iptv_logo_updater/
├── update_channel_logos.py     # Main script
├── get_uk_logos.py             # Script to fetch UK logo filenames from GitHub
├── uk_tv_logos.txt             # Generated list of UK TV logo filenames and URLs
├── specific_channel_fixes.json # Configuration for specific channel fixes
├── reports/                    # Directory for reports
│   ├── logo_matching_report.txt
│   └── unmatched_channels.txt
└── README.md                   # This file
```

## Usage

### Basic Usage

```bash
python update_channel_logos.py
```

This will use the default configuration settings defined at the top of the script.

### Advanced Usage

```bash
python update_channel_logos.py --input "path/to/input.xml" --output "path/to/output.xml" --logos "path/to/logos.txt" --fixes "path/to/fixes.json" --reports "path/to/reports/dir"
```

### Updating Logo List

The repository includes a script to automatically fetch the latest UK TV logo filenames and URLs from the tv-logo/tv-logos GitHub repository:

```bash
python get_uk_logos.py
```

This script will:
- Connect to the tv-logo/tv-logos GitHub repository API
- Fetch all PNG files in the united-kingdom directory
- Generate/update the `uk_tv_logos.txt` file with logo filenames and their download URLs

Run this script periodically to ensure your logo list stays up to date with newly added logos.

## Configuration

You can configure the script in three ways:

1. **Environment variables**: Create a `.env` file based on the provided `.env.example` template.
2. **Edit the script**: Modify the `DEFAULT_CONFIG` dictionary at the top of the script.
3. **Command-line arguments**: Override the default settings using command-line arguments.

### Default Configuration Variables

- `input_xml`: Path to the input XML file
- `output_xml`: Path to the output XML file
- `input_m3u`: Path to the input M3U file
- `output_m3u`: Path to the output M3U file
- `logo_list_file`: Path to the file containing logo filenames and URLs
- `specific_fixes_file`: Path to the JSON file containing specific channel fixes
- `reports_dir`: Directory to store reports

### Environment Variables

The script supports the following environment variables in a `.env` file:

- `DROPBOX_REFRESH_TOKEN`: OAuth refresh token for Dropbox API access
- `DROPBOX_APP_KEY`: Dropbox API app key
- `DROPBOX_APP_SECRET`: Dropbox API app secret
- `DROPBOX_PATH`: Path in Dropbox where to upload files
- `INPUT_XML`: Path to the input XML file
- `OUTPUT_XML`: Path to the output XML file
- `INPUT_M3U`: Path to the input M3U file
- `OUTPUT_M3U`: Path to the output M3U file
- `LOGO_LIST_FILE`: Path to the logo list file
- `SPECIFIC_FIXES_FILE`: Path to the specific fixes file
- `REPORTS_DIR`: Directory to store reports

Create a `.env` file based on the provided `.env.example` template:

## Logo List File Format

The logo list file should contain one logo per line, with the filename and URL separated by a pipe character (`|`):

```
logo-filename.png|https://path/to/logo/on/github
```

## Specific Fixes File Format

The specific fixes file is a JSON file mapping channel IDs to logo URLs:

```json
{
    "channel.id": "https://path/to/logo.png",
    "another.channel.id": "https://path/to/another/logo.png"
}
```

## Generated Reports

The script generates two reports:

1. `logo_matching_report.txt`: Lists all channels that were successfully matched with logos
2. `unmatched_channels.txt`: Lists channels that couldn't be matched and might need specific fixes

## Deployment

For automated execution, set up a cronjob on your server:

```bash
# Example crontab entry (runs daily at 3 AM)
0 3 * * * python /path/to/iptv_logo_updater/update_channel_logos.py --input "/path/to/IPTVBoss/Default.xml" --output "/path/to/Threadfin/guide.xml"
```

## Future Development Plans

Future enhancements to the IPTV Channel Logo Updater will focus on making the system more dynamic and self-maintaining:

### Planned Improvements

1. **Dynamic GitHub Repository Integration** (Partially Implemented)
   - ✅ Automatically scan the tv-logo/tv-logos GitHub repository for available logos (implemented via `get_uk_logos.py`)
   - ✅ Build and maintain a local cache of all available logos (implemented for UK logos)
   - ❌ Periodically refresh the cache to capture new logos as they're added (not yet implemented)
   - ❌ Expand to include other countries/directories beyond UK logos

2. **Intelligent Channel-to-Logo Matching**
   - Implement a multi-stage matching algorithm:
     - Normalized exact matching
     - Substring matching
     - Edit-distance (Levenshtein) for fuzzy matching
     - Confidence scoring system for matches
   - This would eliminate the need for the predefined mapping dictionary

3. **Self-Learning Capabilities**
   - Track successful matches to improve future matching accuracy
   - Learn from manual corrections in the specific fixes file
   - Build a history of channel name variations to improve matching

4. **Performance Optimizations**
   - Caching mechanisms to avoid repeated API calls
   - Parallel processing for large channel lists
   - Incremental updates to avoid reprocessing everything

These improvements would make the system more adaptable to changes in both channel lineups and available logos, reducing manual maintenance needs while increasing matching accuracy.
