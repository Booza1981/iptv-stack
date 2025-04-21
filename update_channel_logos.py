#!/usr/bin/env python3
"""
IPTV Channel Logo Updater for XML and M3U (v3)
==============================================
Updates channel logos in IPTV XML/M3U files using automatic matching
and specific fixes. Uses tvg-id mapping for efficiency if processing both.
"""

import xml.etree.ElementTree as ET
import re
import os
import json
import argparse
from pathlib import Path
import requests
import io
from datetime import datetime # Added import
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# --- Add chardet dependency check ---
try:
    import chardet
except ImportError:
    chardet = None
    # print("Warning: 'chardet' library not found...") # Optional warning

# Assuming dropbox_utils.py is in the same directory or accessible
try:
    from dropbox_utils import get_dropbox_client, upload_to_dropbox
    dropbox_available = True
except ImportError:
    print("Warning: dropbox_utils.py not found. Dropbox upload will be disabled.")
    dropbox_available = False
    # Define dummy functions if needed elsewhere, though upload logic checks flag
    def get_dropbox_client(token): return None
    def upload_to_dropbox(dbx, local, remote): return False


# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_CONFIG = {
    "input_xml": os.environ.get("INPUT_XML", r"https://tinyurl.com/293kjj9g"),
    "output_xml": os.environ.get("OUTPUT_XML", r"C:\Users\beuzi\Desktop\IPTVBoss Outputs\Default_final.xml"),
    "input_m3u": os.environ.get("INPUT_M3U", "https://tinyurl.com/228mlo2g"), # Set to M3U URL/path or None
    "output_m3u": os.environ.get("OUTPUT_M3U", r"C:\Users\beuzi\Desktop\IPTVBoss Outputs\Default_final.m3u"),
    "logo_list_file": os.environ.get("LOGO_LIST_FILE", "uk_tv_logos.txt"), # Optional path
    "specific_fixes_file": os.environ.get("SPECIFIC_FIXES_FILE", "specific_channel_fixes.json"), # Optional path
    "reports_dir": os.environ.get("REPORTS_DIR", "reports"),
    "dropbox_oauth": {
        "refresh_token": os.environ.get("DROPBOX_REFRESH_TOKEN", ""), # Get from environment variable
        "app_key": os.environ.get("DROPBOX_APP_KEY", ""), # Get from environment variable
        "app_secret": os.environ.get("DROPBOX_APP_SECRET", "") # Get from environment variable
    },
    "dropbox_path": os.environ.get("DROPBOX_PATH", "/") # Directory in Dropbox or None
}

# ============================================================================
# Helper Functions (Download, Normalize, Mapping, Logo URL)
# ============================================================================

def download_content(url):
    # ... (Keep the improved download_content function from previous version) ...
    """Downloads content from a URL, handling redirects."""
    print(f"Attempting to download content from: {url}")
    try:
        response = requests.get(url, timeout=30, headers={'User-Agent': 'IPTVLogoUpdater/1.0'})
        response.raise_for_status()
        print(f"Successfully downloaded content (status code: {response.status_code}). Final URL: {response.url}")
        content = response.content
        text_content = None
        detected_encoding = None
        try:
            # Try chardet if available
            if chardet:
                detected_encoding = chardet.detect(content)['encoding']
            # Use response encoding if available and chardet didn't find one
            if not detected_encoding:
                 detected_encoding = response.encoding
            # Fallback to utf-8
            if not detected_encoding:
                 detected_encoding = 'utf-8'

            text_content = content.decode(detected_encoding, errors='replace')
            print(f"Decoded using: {detected_encoding}")
        except Exception as decode_err:
            print(f"Warning: Error decoding content ({decode_err}). Falling back to utf-8 with replace.")
            text_content = content.decode('utf-8', errors='replace')
        return text_content

    except requests.exceptions.Timeout: print(f"Error: Request timed out for {url}"); return None
    except requests.exceptions.RequestException as e: print(f"Error downloading content from {url}: {e}"); return None
    except Exception as e: print(f"An unexpected error occurred during download: {e}"); return None

def normalize_channel_name(name):
    # ... (Keep as is) ...
    """Normalize channel names for better matching"""
    if not name: return ""
    name = name.lower()
    name = re.sub(r'\(directs\)|\s*-\s*(sd|hd|fhd|uhd)|\s+uk$', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def get_logo_mapping():
    # ... (keep as is - loads your extensive mapping) ...
    return {
       "discovery": "discovery-channel-uk.png", "discoverychannel": "discovery-channel-uk.png", "discoveryhistory": "discovery-history-uk.png", "discoveryscience": "discovery-science-uk.png", "discoveryturbo": "discovery-turbo-uk.png", "discoverydmax": "dmax-uk.png", "dmax": "dmax-uk.png", "investigationdiscovery": "investigation-discovery-uk.png", "animalplanet": "animal-planet-uk.png",
        "skydocumentaries": "sky-documentaries-uk.png", "skynature": "sky-nature-uk.png", "skyhistory": "sky-history-uk.png", "skyhistory2": "sky-history-2-uk.png", "skycrime": "sky-crime-uk.png", "skyatlantic": "sky-atlantic-uk.png", "skyaction": "sky-cinema-action-uk.png", "skyanimation": "sky-cinema-animation-uk.png", "skycinemacomedy": "sky-cinema-comedy-uk.png", "skydrama": "sky-cinema-drama-uk.png", "skyfamily": "sky-cinema-family-uk.png", "skyscifihorror": "sky-cinema-sci-fi-and-horror-uk.png", "skypremiere": "sky-cinema-premiere-uk.png", "skyselect": "sky-cinema-select-uk.png", "skygreats": "sky-cinema-greats-uk.png", "skyhits": "sky-cinema-hits-uk.png", "skythriller": "sky-cinema-thriller-uk.png", "skycomedy": "sky-comedy-uk.png", "skyarts": "sky-arts-uk.png", "skymax": "sky-max-uk.png", "skymix": "sky-mix-uk.png", "skyreplay": "sky-replay-uk.png", "skywitness": "sky-witness-uk.png", "skykids": "sky-kids-uk.png", "skyscifi": "sky-sci-fi-uk.png", "skyshowcase": "sky-showcase-uk.png",
        "natgeo": "national-geographic-uk.png", "nationalgeography": "national-geographic-uk.png", "natgeowild": "national-geographic-wild-uk.png", "nationalgeowild": "national-geographic-wild-uk.png",
        "bbcone": "bbc-one-uk.png", "bbctwo": "bbc-two-uk.png", "bbcthree": "bbc-three-uk.png", "bbcfour": "bbc-four-uk.png", "cbbc": "bbc-cbbc-uk.png", "cbeebies": "bbc-cbeebies-uk.png", "bbcnews": "bbc-news-uk.png", "bbcparliament": "bbc-parliament-uk.png", "bbcworldnews": "bbc-world-news-uk.png",
        "itv1": "itv-1-uk.png", "itv2": "itv-2-uk.png", "itv3": "itv-3-uk.png", "itv4": "itv-4-uk.png", "itvbe": "itv-be-uk.png",
        "channel4": "channel-4-uk.png", "more4": "4-more-uk.png", "e4": "e-4-uk.png", "e4extra": "e-4-extra-uk.png", "4seven": "4-seven-uk.png", "film4": "film-4-uk.png",
        "channel5": "channel-5-uk.png", "5action": "5-action-uk.png", "5select": "5-select-uk.png", "5star": "5-star-uk.png", "5usa": "5-usa-uk.png", "fiveusa": "5-usa-uk.png",
        "cartoonnetwork": "cartoon-network-uk.png", "cartoonito": "cartoonito-uk.png", "boomerang": "boomerang-uk.png", "nickelodeon": "nickelodeon-uk.png", "nickjunior": "nick-jr-uk.png", "nickjrtoo": "nick-jr-too-uk.png", "nicktoons": "nick-toons-uk.png", "disneychannel": "disney-channel-uk.png", "disneyjunior": "disney-jr-uk.png", "disneyjr": "disney-jr-uk.png", "disneyxd": "disney-xd-uk.png", "babytv": "baby-tv-uk.png", "pop": "pop-uk.png", "popmax": "pop-max-uk.png",
        "skysportsnews": "sky-sports-news-uk.png", "skysportsmainevent": "sky-sports-main-event-uk.png", "skysportsfootball": "sky-sports-football-uk.png", "skysportspremiereleague": "sky-sports-premier-league-uk.png", "skysportsf1": "sky-sports-f1-uk.png", "skysportsgolf": "sky-sports-golf-uk.png", "skysportsplus": "sky-sports-plus-hz-uk.png", "skysportsaction": "sky-sports-action-uk.png", "skysportsarena": "sky-sports-arena-uk.png", "skysportstennis": "sky-sports-tennis-uk.png", "skysportscricket": "sky-sports-cricket-uk.png", "skysportsmix": "sky-sports-mix-uk.png", "skysportsracing": "sky-sports-racing-uk.png",
        "tntsports1": "tnt-sports-1-uk.png", "tntsports2": "tnt-sports-2-uk.png", "tntsports3": "tnt-sports-3-uk.png", "tntsports4": "tnt-sports-4-uk.png", "tntsportsultimate": "tnt-sports-ultimate-uk.png",
        "eurosport1": "eurosport-1-uk.png", "eurosport2": "eurosport-2-uk.png", "eurosport4k": "eurosport-4k-uk.png",
        "premiersports1": "premier-sports-1-uk.png", "premiersports2": "premier-sports-2-uk.png", "laligatv": "laliga-tv-uk.png", "mutv": "mutv-uk.png", "lfctv": "lfctv-uk.png", "liverpoolfctv": "lfctv-uk.png",
        "skynews": "sky-news-uk.png", "aljazeera": "aljazeera-uk.png", "arisenews": "arise-news-uk.png", "gbnews": "gb-news-uk.png", "talkTV": "talk-tv-uk.png",
        "gold": "gold-uk.png", "comedycentral": "comedy-central-uk.png", "dave": "dave-uk.png", "davejavvu": "dave-ja-vu-uk.png", "quest": "quest-uk.png", "questred": "quest-red-uk.png", "tlc": "tlc-uk.png", "drama": "drama-uk.png", "yesterday": "yesterday-uk.png", "eden": "eden-uk.png", "foodnetwork": "food-network-uk.png", "hgtv": "hgtv-uk.png", "syfy": "syfy-uk.png", "w": "w-network-uk.png", "challenge": "challenge-uk.png", "horseandcountry": "horse-and-country-uk.png", "smithsonian": "smithsonian-channel-uk.png", "crime": "crime-and-investigation-uk.png", "crimeandinvestigationnetwork": "crime-and-investigation-uk.png", "together": "together-tv-uk.png", "blaze": "blaze-uk.png", "realityxtra": "reality-xtra-uk.png", "s4c": "s4c-uk.png", "stv": "stv-uk.png", "boxnation": "box-nation-uk.png", "boxhits": "box-hits-uk.png", "kerrangtv": "kerrang-tv-uk.png", "mtvbase": "mtv-base-uk.png", "mtvhits": "mtv-hits-uk.png", "mtvmusic": "mtv-music-uk.png", "mtv": "mtv-uk.png", "now70s": "now-70s-uk.png", "now80s": "now-80s-uk.png", "now90s": "now-90s-uk.png", "clublandtv": "clubland-uk.png", "rtenewsnow": "rte-news-now-uk.png", "lifetime": "lifetime-uk.png", "movies24": "movies-24-uk.png", "comedyxtra": "comedy-central-extra-uk.png", "legend": "legend-uk.png", "greataction": "great-action-uk.png", "greatmovies": "great-movies-uk.png", "alibi": "alibi-uk.png", "mtvclassic": "mtv-classic-uk.png"
    }


def get_logo_url(channel_name, logo_files, mappings):
    # ... (Keep improved version from previous step) ...
    """Find the best logo URL for a channel name"""
    normalized_name = normalize_channel_name(channel_name)
    if not normalized_name: return None

    # Check direct mapping first
    if normalized_name in mappings:
        logo_filename = mappings[normalized_name]
        for logo_file in logo_files:
            try:
                name, url = logo_file.split('|', 1)
                if name == logo_filename: return url
            except ValueError: continue

    # Fallback to partial matching
    best_match_score = 0
    best_match_url = None
    for pattern, logo_filename in mappings.items():
         score = 0
         if pattern in normalized_name: score = len(pattern)
         elif normalized_name in pattern: score = len(normalized_name)
         if score > best_match_score:
             for logo_file in logo_files:
                 try:
                     name, url = logo_file.split('|', 1)
                     if name == logo_filename:
                         best_match_score = score
                         best_match_url = url
                         break
                 except ValueError: continue
    return best_match_url

# --- NEW Helper Function for Efficiency ---
def build_tvg_id_map_from_xml(final_xml_path):
    """Reads the final processed XML and builds a map of tvg-id to logo src."""
    print(f"Building tvg-id to logo map from: {final_xml_path}")
    tvg_id_map = {}
    if not final_xml_path or not os.path.exists(final_xml_path):
        print("Warning: Final XML path not provided or file not found. Cannot build tvg-id map.")
        return tvg_id_map

    try:
        tree = ET.parse(final_xml_path)
        root = tree.getroot()
        count = 0
        for channel in root.findall('.//channel'):
            channel_id = channel.get('id')
            icon_elem = channel.find('icon')
            if channel_id and icon_elem is not None:
                logo_src = icon_elem.get('src')
                if logo_src:
                    tvg_id_map[channel_id] = logo_src
                    count += 1
        print(f"Built map with {count} tvg-id entries.")
    except ET.ParseError as e:
        print(f"Error parsing final XML file {final_xml_path} to build map: {e}")
    except Exception as e:
        print(f"An unexpected error occurred building tvg-id map: {e}")

    return tvg_id_map
# --- End of New Helper ---

# ============================================================================
# Main Processing Functions (XML, Fixes, M3U)
# ============================================================================
# Ensure these imports are present at the top of your script
import xml.etree.ElementTree as ET
import re
import os
import io

# Make sure get_logo_mapping and get_logo_url are defined before this function or imported

def update_xml_with_logos(xml_content_string, logo_files_list, output_file, reports_dir):
    """Update channel icons in the XML content string with matching logos"""
    print("Processing downloaded XML content...")

    # --- Initialize logo_files CORRECTLY ---
    logo_files = [] # Initialize as an empty list
    if logo_files_list: # Check if a file path/name was provided
        if os.path.exists(logo_files_list):
            print(f"Using logo list: {logo_files_list}")
            try:
                with open(logo_files_list, 'r', encoding='utf-8') as f:
                    logo_files = f.read().splitlines() # Assign loaded lines
                print(f"Loaded {len(logo_files)} entries from logo list.")
            except Exception as e:
                print(f"Warning: Error reading logo list file {logo_files_list}: {e}. Proceeding without automatic matching.")
                logo_files = [] # Ensure it's an empty list on error
        else:
             print(f"Warning: Logo list file not found: '{logo_files_list}'. Skipping automatic logo matching.")
             logo_files = [] # Ensure it's an empty list if file not found
    else:
        print("Warning: No logo list file provided. Skipping automatic logo matching.")
        logo_files = [] # Ensure it's an empty list if no path provided

    # --- Ensure Reports Directory Exists ---
    try:
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            print(f"Created reports directory: {reports_dir}")
    except Exception as e:
        print(f"Error creating reports directory '{reports_dir}': {e}")
        # Decide if you want to stop or continue without reports
        # return None, 0, 0 # Option to stop

    # --- Parse XML and Fix Ampersands ---
    tree = None
    root = None
    try:
        xml_file_like_object = io.StringIO(xml_content_string)
        tree = ET.parse(xml_file_like_object)
        root = tree.getroot()
        print("Successfully parsed downloaded XML content.")

        potentially_fixed_names = 0
        print("Checking for raw ampersands in display-names...")
        if root is not None:
            for channel in root.findall('.//channel'):
                channel_id_for_log = channel.get('id', 'N/A')
                for i, display_name_elem in enumerate(channel.findall('display-name')):
                    if display_name_elem.text and '&' in display_name_elem.text:
                        original_text = display_name_elem.text
                        fixed_text = re.sub(r'&(?!(?:lt|gt|amp|apos|quot);|#\d+;)', r'&amp;', original_text)
                        if original_text != fixed_text:
                            display_name_elem.text = fixed_text
                            potentially_fixed_names += 1
                            # Optional detailed log:
                            # print(f"  Fixed raw '&' in display-name {i+1} for channel ID '{channel_id_for_log}': '{original_text}' -> '{fixed_text}'")
            if potentially_fixed_names > 0:
                 print(f"Attempted to fix raw '&' in {potentially_fixed_names} display-name(s).")
            else:
                 print("No raw ampersands found needing fixing in display-names.")
        else:
            print("Error: XML root not found after parsing. Cannot fix ampersands.")
            return None, 0, 0 # Exit if root is None

    except ET.ParseError as e:
        print(f"Error parsing downloaded XML content: {e}")
        return None, 0, 0
    except Exception as e:
        print(f"An unexpected error occurred during XML parsing or fixing: {e}")
        return None, 0, 0

    # --- Sanity check after try-except ---
    if root is None or tree is None:
         print("Error: XML tree/root is not valid after parsing attempt.")
         return None, 0, 0

    # --- Logo Matching Logic ---
    mappings = get_logo_mapping() # Ensure this function is defined/imported
    matched_channels = 0
    total_channels = 0
    matched_logos = {}
    unmatched_channels = []

    # <<< This is the line from the traceback (approx line 228 in original function)
    # By this point, logo_files MUST be defined (either loaded list or [])
    print(f"Processing {len(root.findall('.//channel'))} channels found in XML...")
    if logo_files:
        print(f"Attempting logo matching using {len(logo_files)} logo file entries...")
        for channel in root.findall('.//channel'):
            total_channels += 1
            channel_id = channel.get('id', '')
            display_names = channel.findall('display-name')
            # Use the (potentially fixed) text from the first display-name
            main_display_name = display_names[0].text if display_names and display_names[0].text else channel_id

            logo_url = get_logo_url(main_display_name, logo_files, mappings) # Ensure get_logo_url is defined/imported

            # Optional: Add fallback logic if needed
            # if not logo_url and channel_id:
            #     logo_url = get_logo_url(channel_id.split('.')[0], logo_files, mappings) # Example fallback

            if logo_url:
                icon_elem = channel.find('icon')
                if icon_elem is None: icon_elem = ET.SubElement(channel, 'icon')
                icon_elem.set('src', logo_url)
                matched_channels += 1
                matched_logos[channel_id or main_display_name] = {'name': main_display_name, 'logo': logo_url.split('/')[-1]}
            else:
                unmatched_channels.append({'id': channel_id, 'name': main_display_name})
    else:
        # This block executes if logo_files is empty []
        print("Logo matching skipped (logo list file not loaded or empty).")
        # Still count channels and populate unmatched list
        for channel in root.findall('.//channel'):
             total_channels += 1
             channel_id = channel.get('id', '')
             display_names = channel.findall('display-name')
             main_display_name = display_names[0].text if display_names and display_names[0].text else channel_id
             unmatched_channels.append({'id': channel_id, 'name': main_display_name})

    print(f"Finished processing channels. Total: {total_channels}") # Consolidated count

    # --- Write Intermediate File ---
    intermediate_file = output_file.replace('.xml', '_intermediate.xml')
    try:
        tree.write(intermediate_file, encoding='UTF-8', xml_declaration=True, short_empty_elements=False)
        print(f"Intermediate XML saved to {intermediate_file}")
    except Exception as e:
        print(f"Error writing intermediate XML file {intermediate_file}: {e}")
        # Return counts found so far, but indicate failure by returning None for the path
        return None, matched_channels, total_channels

    print(f"Matched {matched_channels} logo(s) automatically (XML)")

    # --- Report Generation ---
    # (Make sure report writing uses safe access methods as shown previously)
    try:
        # --- Matches Report ---
        matches_report = os.path.join(reports_dir, 'logo_matching_report_xml.txt')
        with open(matches_report, 'w', encoding='utf-8') as f:
            f.write("Channel ID | Display Name | Matched Logo\n")
            f.write("-" * 60 + "\n")
            for channel_id, info in matched_logos.items():
                name_to_encode = info.get('name', '') or "N/A"
                logo_to_encode = info.get('logo', '') or "N/A"
                safe_name = name_to_encode.encode('ascii', 'replace').decode('ascii')
                safe_logo = logo_to_encode.encode('ascii', 'replace').decode('ascii')
                f.write(f"{channel_id or 'N/A'} | {safe_name} | {safe_logo}\n")
        print(f"XML Matching report saved to {matches_report}")

        # --- Unmatched Report ---
        unmatched_report = os.path.join(reports_dir, 'unmatched_channels_xml.txt')
        with open(unmatched_report, 'w', encoding='utf-8') as f:
            f.write("Channel ID | Display Name\n")
            f.write("-" * 40 + "\n")
            # Use the consolidated unmatched_channels list
            for channel in unmatched_channels:
                id_to_encode = channel.get('id', '') or "N/A"
                name_to_encode = channel.get('name', '') or "N/A"
                safe_id = id_to_encode.encode('ascii', 'replace').decode('ascii')
                safe_name = name_to_encode.encode('ascii', 'replace').decode('ascii')
                f.write(f"{safe_id} | {safe_name}\n")
        print(f"XML Unmatched channels report saved to {unmatched_report}")

    except Exception as e:
        print(f"Warning: Failed to write XML report due to: {e}")

    # Return results
    return intermediate_file, matched_channels, total_channels

def update_m3u_with_logos(m3u_content_string, logo_files_list, specific_fixes, tvg_id_logo_map, output_m3u_path, reports_dir): # <-- Added tvg_id_logo_map
    """Updates tvg-logo attributes in M3U content string, using tvg-id map first."""
    print(f"Processing M3U content...")
    logo_files = [] # Initialize empty list
    if logo_files_list and os.path.exists(logo_files_list):
        print(f"Using logo list: {logo_files_list}")
        try:
            with open(logo_files_list, 'r', encoding='utf-8') as f: logo_files = f.read().splitlines()
        except Exception as e: print(f"Warning: Error reading logo list file {logo_files_list}: {e}. Proceeding without automatic matching for new channels.")
    else:
         print("Warning: Logo list file not provided or not found. Will only use XML map and specific fixes for M3U.")

    print(f"Using {len(specific_fixes)} specific fixes.")
    print(f"Using {len(tvg_id_logo_map)} logos mapped from XML.")

    if not os.path.exists(reports_dir): os.makedirs(reports_dir)

    mappings = get_logo_mapping() # Still need for fallback
    output_lines = []
    total_channels, mapped_channels, matched_channels, fixed_channels = 0, 0, 0, 0
    m3u_matched_logos = {}
    m3u_unmatched_channels = []

    lines = m3u_content_string.splitlines()
    if not lines or not lines[0].strip().startswith("#EXTM3U"):
        print("Warning: Input does not start with #EXTM3U.")
        # Optionally add it: output_lines.append("#EXTM3U")


    for i, line in enumerate(lines):
        original_line = line # Keep original for appending if no change
        line = line.strip()

        if line.startswith("#EXTINF:"):
            total_channels += 1
            output_lines.append(original_line) # Append original first, may replace later
            current_line_index = len(output_lines) - 1

            tvg_id_match = re.search(r'tvg-id="([^"]*)"', line, re.IGNORECASE)
            tvg_name_match = re.search(r'tvg-name="([^"]*)"', line, re.IGNORECASE)
            tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line, re.IGNORECASE)
            comma_name_match = re.search(r'.*?,(.*)$', line)

            channel_id = tvg_id_match.group(1) if tvg_id_match else None
            channel_name = tvg_name_match.group(1) if tvg_name_match else (comma_name_match.group(1).strip() if comma_name_match else None)
            if not channel_name and channel_id: channel_name = channel_id

            new_logo_url = None
            update_source = None # Track how logo was found: 'map', 'fix', 'match'

            # --- Logo Finding Logic ---
            # 1. Check tvg-id map from XML
            if channel_id and channel_id in tvg_id_logo_map:
                new_logo_url = tvg_id_logo_map[channel_id]
                update_source = 'map'
                mapped_channels += 1
            else:
                # 2. Check Specific Fixes (if not found in map)
                if channel_id and channel_id in specific_fixes:
                    new_logo_url = specific_fixes[channel_id]
                    update_source = 'fix'
                    fixed_channels += 1
                else:
                    # 3. Try Automatic Matching (if not in map or fixed, and logo list exists)
                    if channel_name and logo_files:
                        logo_url_match = get_logo_url(channel_name, logo_files, mappings)
                        if logo_url_match:
                            new_logo_url = logo_url_match
                            update_source = 'match'
                            matched_channels += 1

            # --- Update Line if Logo Found ---
            if new_logo_url:
                m3u_matched_logos[channel_id or channel_name] = {'name': channel_name, 'logo': new_logo_url.split('/')[-1], 'source': update_source}
                if tvg_logo_match:
                    updated_line = re.sub(r'tvg-logo="([^"]*)"', f'tvg-logo="{new_logo_url}"', line, flags=re.IGNORECASE)
                else: # Add tag
                    if tvg_name_match: insert_pos = tvg_name_match.end(); updated_line = line[:insert_pos] + f' tvg-logo="{new_logo_url}"' + line[insert_pos:]
                    elif comma_name_match: insert_pos = comma_name_match.start(1) - 1; updated_line = line[:insert_pos] + f' tvg-logo="{new_logo_url}"' + line[insert_pos:]
                    else: updated_line = line + f' tvg-logo="{new_logo_url}"'
                output_lines[current_line_index] = updated_line # Replace original line
            elif channel_name: # Record as unmatched only if name existed
                 m3u_unmatched_channels.append({'id': channel_id, 'name': channel_name})

        else: # Not an #EXTINF line, just append
            output_lines.append(original_line)


    # --- Write Output M3U ---
    try:
        output_dir = os.path.dirname(output_m3u_path)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir); print(f"Created output directory: {output_dir}")
        with open(output_m3u_path, 'w', encoding='utf-8') as f: f.write('\n'.join(output_lines))
        print(f"M3U Update Summary: Used XML Map={mapped_channels}, Matched New={matched_channels}, Fixed={fixed_channels} out of {total_channels} channels")
        print(f"Updated M3U saved to: {output_m3u_path}")
    except Exception as e: print(f"Error writing updated M3U file {output_m3u_path}: {e}"); return 0, 0

    # --- Generate M3U Reports ---
    # ... (Modify report generation to include 'source') ...
    try:
        m3u_matches_report = os.path.join(reports_dir, 'logo_matching_report_m3u.txt')
        with open(m3u_matches_report, 'w', encoding='utf-8') as f:
            f.write("Channel ID/Name | Display Name | Matched Logo | Source\n")
            f.write("-" * 70 + "\n")
            for channel_id, info in m3u_matched_logos.items():
                 safe_name = info['name'].encode('ascii', 'replace').decode('ascii') if info['name'] else "N/A"
                 safe_logo = info['logo'].encode('ascii', 'replace').decode('ascii') if info['logo'] else "N/A"
                 source = info['source'] if 'source' in info else 'N/A'
                 f.write(f"{channel_id} | {safe_name} | {safe_logo} | {source}\n")
        print(f"M3U Matching report saved to {m3u_matches_report}")

        m3u_unmatched_report = os.path.join(reports_dir, 'unmatched_channels_m3u.txt')
        with open(m3u_unmatched_report, 'w', encoding='utf-8') as f:
            f.write("Channel ID | Display Name\n")
            f.write("-" * 40 + "\n")
            for channel in m3u_unmatched_channels:
                 safe_id = channel['id'].encode('ascii', 'replace').decode('ascii') if channel['id'] else "N/A"
                 safe_name = channel['name'].encode('ascii', 'replace').decode('ascii') if channel['name'] else "N/A"
                 f.write(f"{safe_id} | {safe_name}\n")
        print(f"M3U Unmatched channels report saved to {m3u_unmatched_report}")
    except Exception as e:
        print(f"Warning: Failed to write M3U report due to: {e}")


    # Return combined count of updated logos
    return mapped_channels + matched_channels + fixed_channels, total_channels

def fix_specific_channels(xml_file, specific_fixes, output_file):
    """Fix specific channel logos in the XML file using loaded fixes"""
    print(f"Attempting to apply {len(specific_fixes)} specific fixes to: {xml_file}")

    # --- Input Validation ---
    if not os.path.exists(xml_file):
        print(f"Error: Intermediate file not found: {xml_file}. Cannot apply specific fixes.")
        # If intermediate doesn't exist, copy won't work either. Indicate failure.
        return 0

    # --- Handle No Fixes Case ---
    if not specific_fixes:
        print("No specific fixes loaded or provided. Skipping XML fix step.")
        # Copy intermediate to final only if intermediate exists
        try:
            # Ensure shutil is imported if using copyfile (add 'import shutil' at the top)
            import shutil
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                 os.makedirs(output_dir)
            shutil.copyfile(xml_file, output_file)
            print(f"Copied intermediate file to final output (no fixes applied): {output_file}")
            return 0 # 0 fixes applied
        except Exception as e:
            print(f"Error copying intermediate file {xml_file} to {output_file}: {e}")
            # If copy fails, report 0 fixes and maybe signal error differently if needed
            return 0

    # --- Ensure Output Directory Exists ---
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory for final XML: {output_dir}")
        except Exception as e:
             print(f"Error creating output directory '{output_dir}': {e}")
             return 0 # Indicate failure

    # --- Parse Intermediate XML ---
    tree = None
    root = None
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing intermediate XML file {xml_file}: {e}")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred reading {xml_file}: {e}")
        return 0

    if root is None or tree is None:
        print(f"Error: Failed to get XML root/tree from {xml_file}. Cannot apply fixes.")
        return 0

    # --- Apply Fixes ---
    fixed_count = 0
    print("Applying specific channel fixes...")
    for channel in root.findall('.//channel'):
        channel_id = channel.get('id', '')
        if channel_id and channel_id in specific_fixes: # Check channel_id exists and is in fixes
            new_logo_url = specific_fixes[channel_id]
            icon_elem = channel.find('icon')
            log_prefix = f"  Channel ID '{channel_id}':" # For logging

            if icon_elem is None:
                icon_elem = ET.SubElement(channel, 'icon')
                print(f"{log_prefix} Added icon tag with fixed logo.")
            # else: # Optionally log updates too
            #     print(f"{log_prefix} Updating existing icon tag with fixed logo.")

            icon_elem.set('src', new_logo_url) # ET.write should handle attribute escaping
            fixed_count += 1

    if fixed_count > 0:
        print(f"Applied {fixed_count} specific fixes to the XML tree.")
    else:
        print("No applicable specific fixes found for channels in the XML.")

    # --- Write Final XML ---
    try:
        tree.write(output_file, encoding='UTF-8', xml_declaration=True, short_empty_elements=False)
        print(f"Final XML file with specific fixes saved to {output_file}")
    except Exception as e:
        print(f"Error writing final XML file {output_file}: {e}")
        # Depending on desired outcome, you might still return fixed_count
        # or indicate write failure more strongly.
        # For now, return the count of fixes applied in memory.
        return fixed_count

    return fixed_count # Return the number of fixes successfully applied

# ============================================================================
# Argument Parser
# ============================================================================
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Update IPTV channel logos in XML and/or M3U files')

    # --- Inputs ---
    parser.add_argument('--input-xml', help='Input XML URL or file path', default=DEFAULT_CONFIG.get('input_xml'))
    parser.add_argument('--input-m3u', help='Input M3U URL or file path', default=DEFAULT_CONFIG.get('input_m3u'))

    # --- Outputs ---
    parser.add_argument('--output-xml', help='Output XML file path', default=DEFAULT_CONFIG.get('output_xml'))
    parser.add_argument('--output-m3u', help='Output M3U file path', default=DEFAULT_CONFIG.get('output_m3u'))
    # --- ADD THIS LINE BACK ---
    parser.add_argument('--reports', dest='reports_dir',
                        help='Directory to store reports',
                        default=DEFAULT_CONFIG.get('reports_dir', 'reports'))
    # --------------------------

    # --- Data Files (Optional) ---
    parser.add_argument('--logos', dest='logo_list_file',
                        help='Logo list file path (format: filename|url)',
                        default=DEFAULT_CONFIG.get('logo_list_file')) # REMOVED required=True
    parser.add_argument('--fixes', dest='specific_fixes_file',
                        help='Specific fixes JSON file path',
                        default=DEFAULT_CONFIG.get('specific_fixes_file')) # REMOVED required=True

    # --- Dropbox (Optional) ---
    parser.add_argument('--dropbox-oauth', help='Dropbox OAuth configuration (JSON string or path to JSON file)', default=json.dumps(DEFAULT_CONFIG.get('dropbox_oauth')))
    parser.add_argument('--dropbox-path', help='Path (directory) in Dropbox', default=DEFAULT_CONFIG.get('dropbox_path'))

    args = parser.parse_args()

    # --- Validation ---
    if args.input_xml and not args.output_xml: parser.error("--output-xml required with --input-xml")
    if args.input_m3u and not args.output_m3u: parser.error("--output-m3u required with --input-m3u")
    if not args.input_xml and not args.input_m3u: parser.error("Either --input-xml or --input-m3u must be provided.")
    # Check reports_dir exists now that args.reports_dir is guaranteed to be set
    if not hasattr(args, 'reports_dir') or not args.reports_dir:
         parser.error("Reports directory argument is missing or empty.") # Should not happen with default
    if args.dropbox_oauth and not args.dropbox_path: parser.error("--dropbox-path required with --dropbox-oauth")
    
    # Process dropbox_oauth argument - could be a JSON string or path to a file
    if args.dropbox_oauth:
        try:
            if os.path.isfile(args.dropbox_oauth):
                # It's a file path
                with open(args.dropbox_oauth, 'r') as f:
                    args.dropbox_oauth = json.load(f)
            else:
                # It's a JSON string
                args.dropbox_oauth = json.loads(args.dropbox_oauth)
                
            # Validate required fields
            if not all(k in args.dropbox_oauth for k in ['refresh_token', 'app_key', 'app_secret']):
                print("Warning: Dropbox OAuth config missing required fields. Dropbox upload will be disabled.")
                args.dropbox_oauth = None
        except json.JSONDecodeError:
            print("Warning: Invalid Dropbox OAuth JSON. Dropbox upload will be disabled.")
            args.dropbox_oauth = None
        except Exception as e:
            print(f"Warning: Error processing Dropbox OAuth config: {e}. Dropbox upload will be disabled.")
            args.dropbox_oauth = None

    return args

# ============================================================================
# Main Execution
# ============================================================================
def main():
    """Main function to run the script"""
    args = parse_arguments()

    print("=" * 80)
    print("IPTV Channel Logo Updater (XML & M3U)")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # --- Load Specific Fixes Once (if file provided) ---
    specific_fixes = {}
    if args.specific_fixes_file and os.path.exists(args.specific_fixes_file):
        print(f"Loading specific fixes from: {args.specific_fixes_file}")
        try:
            with open(args.specific_fixes_file, 'r', encoding='utf-8') as f:
                specific_fixes = json.load(f)
            print(f"Loaded {len(specific_fixes)} specific fixes.")
        except json.JSONDecodeError as e: print(f"Warning: Error decoding JSON fixes: {e}")
        except Exception as e: print(f"Warning: Error reading fixes file: {e}")
    else:
        print("Skipping specific fixes (file not provided or not found).")
    print("-" * 40)

    # --- Process XML ---
    xml_processed_successfully = False
    intermediate_xml_file = None
    final_xml_output_path = args.output_xml # Store final path for map building

    if args.input_xml and args.output_xml:
        print(f"Processing XML: {args.input_xml} -> {args.output_xml}")
        # Step 0: Download
        xml_content = download_content(args.input_xml)
        if xml_content:
            # Step 1: Auto-match logos
            intermediate_xml_file, _, _ = update_xml_with_logos(
                xml_content, args.logo_list_file, args.output_xml, args.reports_dir
            )
            if intermediate_xml_file:
                # Step 2: Apply specific fixes
                _ = fix_specific_channels( # Use loaded dict
                    intermediate_xml_file, specific_fixes, args.output_xml
                )
                xml_processed_successfully = True # Mark success after fixes applied
            else: print("XML processing failed during logo matching/intermediate file writing.")
        else: print("XML processing failed during download.")
    else: print("Skipping XML processing (input/output not specified).")
    print("-" * 40)


    # --- Build tvg-id Map (if XML was processed) ---
    tvg_id_logo_map = {}
    if xml_processed_successfully:
        tvg_id_logo_map = build_tvg_id_map_from_xml(final_xml_output_path)
    else:
        print("Skipping tvg-id map build (XML not processed successfully).")
    print("-" * 40)

    # --- Process M3U ---
    m3u_processed_successfully = False
    if args.input_m3u and args.output_m3u:
        print(f"\nProcessing M3U: {args.input_m3u} -> {args.output_m3u}")
        # Step 0: Get Content
        m3u_content = None
        if args.input_m3u.startswith(('http://', 'https://')):
            m3u_content = download_content(args.input_m3u)
        elif os.path.exists(args.input_m3u):
            try:
                with open(args.input_m3u, 'r', encoding='utf-8') as f: m3u_content = f.read()
                print(f"Read M3U content from local file: {args.input_m3u}")
            except Exception as e: print(f"Error reading M3U input file: {e}")
        else:
             print(f"Error: M3U input file not found: {args.input_m3u}")

        if m3u_content:
            # Step 1 & 2 Combined: Update logos using map, fixes, and matching
            updated_count, total_m3u = update_m3u_with_logos(
                m3u_content,
                args.logo_list_file,
                specific_fixes,
                tvg_id_logo_map, # Pass the map
                args.output_m3u,
                args.reports_dir
            )
            if updated_count >= 0: # Function returns counts even on write error
                 m3u_processed_successfully = True # Mark as processed if function ran
        else: print("Skipping M3U processing (failed to get content).")
    else: print("Skipping M3U processing (input/output not specified).")
    print("-" * 40)

    # --- Upload to Dropbox ---
    files_to_upload = []
    if xml_processed_successfully and args.output_xml and os.path.exists(args.output_xml):
        files_to_upload.append(args.output_xml)
    if m3u_processed_successfully and args.output_m3u and os.path.exists(args.output_m3u):
        files_to_upload.append(args.output_m3u)

    if dropbox_available and args.dropbox_oauth and args.dropbox_path and files_to_upload:
        print(f"\nStarting Step 3: Uploading to Dropbox directory {args.dropbox_path}")
        # Use the oauth configuration for the client
        dbx = get_dropbox_client(args.dropbox_oauth)

        if dbx:
            upload_success_count = 0
            for local_file_path in files_to_upload:
                try:
                    dropbox_filename = os.path.basename(local_file_path)
                    base_dropbox_path = args.dropbox_path.rstrip('/')
                    full_dropbox_path = f"{base_dropbox_path}/{dropbox_filename}"
                    if not full_dropbox_path.startswith('/'): full_dropbox_path = '/' + full_dropbox_path

                    print(f"Attempting upload: {local_file_path} -> {full_dropbox_path}")
                    if upload_to_dropbox(dbx, local_file_path, full_dropbox_path):
                        print(f"Successfully uploaded: {full_dropbox_path}")
                        upload_success_count += 1
                    else:
                        print(f"Failed to upload: {local_file_path} (upload function returned False)")

                except FileNotFoundError: print(f"Error during Dropbox upload: Local file not found: {local_file_path}")
                except Exception as e: print(f"Error during Dropbox upload of {local_file_path}: {e}")

            if upload_success_count == len(files_to_upload): print("\nAll processed files successfully uploaded to Dropbox.")
            elif upload_success_count > 0: print(f"\n{upload_success_count}/{len(files_to_upload)} files uploaded to Dropbox.")
            else: print("\nNo files were successfully uploaded to Dropbox.")
        else: print("\nSkipping Dropbox upload: Client initialization failed (check OAuth settings).")
    elif files_to_upload: print("\nSkipping Step 3: Dropbox not configured or dropbox_utils not available.")
    else: print("\nSkipping Step 3: No processed files available to upload.")
    print("-" * 40)


    # --- Final Summary ---
    print("\n===== Processing Summary =====")
    if args.input_xml: print(f"XML Output {'(Processed)' if xml_processed_successfully else '(Failed)'}: {args.output_xml or 'N/A'}")
    if args.input_m3u: print(f"M3U Output {'(Processed)' if m3u_processed_successfully else '(Failed)'}: {args.output_m3u or 'N/A'}")
    print(f"Reports saved to: {args.reports_dir}")
    print("==============================")

    # Clean up intermediate XML file
    if intermediate_xml_file and os.path.exists(intermediate_xml_file):
        try:
            os.remove(intermediate_xml_file)
            print(f"\nCleaned up intermediate file: {intermediate_xml_file}")
        except Exception as e: print(f"\nWarning: Could not remove intermediate file: {e}")

if __name__ == "__main__":
    # Ensure necessary imports for main execution block
    # from datetime import datetime # Already imported
    main()
