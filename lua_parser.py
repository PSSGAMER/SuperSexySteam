# lua_parser.py
#
# A standalone script for parsing .lua files to extract depot information.
# This script scans the 'data' directory for .lua files and extracts depot IDs
# and their corresponding decryption keys.

import logging
from pathlib import Path
import sys

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


# =============================================================================
# --- LUA PARSING FUNCTIONS ---
# =============================================================================

def preprocess_lua_line(line):
    """
    Preprocesses a Lua line by removing comments and normalizing whitespace.
    
    Args:
        line (str): Raw line from Lua file
        
    Returns:
        str: Cleaned line with comments removed and whitespace normalized
    """
    # Remove inline comments (everything after --)
    # Handle string literals that might contain -- by doing basic parsing
    in_string = False
    quote_char = None
    i = 0
    
    while i < len(line) - 1:
        char = line[i]
        
        # Track string boundaries
        if not in_string and char in ['"', "'"]:
            in_string = True
            quote_char = char
        elif in_string and char == quote_char:
            # Check if it's escaped
            if i > 0 and line[i-1] != '\\':
                in_string = False
                quote_char = None
        
        # Look for comment start outside of strings
        elif not in_string and char == '-' and line[i+1] == '-':
            line = line[:i]
            break
            
        i += 1
    
    # Normalize whitespace
    return line.strip()


def extract_function_calls(line, function_name):
    """
    Extracts function call arguments from a preprocessed Lua line.
    More robust than regex for handling various formatting styles.
    
    Args:
        line (str): Preprocessed Lua line
        function_name (str): Name of function to match (e.g., 'adddepot', 'addappid')
        
    Returns:
        list or None: List of arguments if function call found, None otherwise
    """
    # Check if line starts with the function name
    if not line.startswith(function_name + '('):
        return None
    
    # Find the opening and closing parentheses
    start_paren = line.find('(')
    if start_paren == -1:
        return None
    
    # Find matching closing parenthesis
    paren_count = 0
    end_paren = -1
    in_string = False
    quote_char = None
    
    for i in range(start_paren, len(line)):
        char = line[i]
        
        # Track string boundaries
        if not in_string and char in ['"', "'"]:
            in_string = True
            quote_char = char
        elif in_string and char == quote_char:
            # Check if it's escaped
            if i > 0 and line[i-1] != '\\':
                in_string = False
                quote_char = None
        
        # Count parentheses outside of strings
        elif not in_string:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    end_paren = i
                    break
    
    if end_paren == -1:
        return None
    
    # Extract arguments string
    args_str = line[start_paren + 1:end_paren].strip()
    if not args_str:
        return []
    
    # Parse arguments (simple comma splitting with string awareness)
    args = []
    current_arg = ""
    in_string = False
    quote_char = None
    
    for char in args_str:
        if not in_string and char in ['"', "'"]:
            in_string = True
            quote_char = char
            current_arg += char
        elif in_string and char == quote_char:
            in_string = False
            quote_char = None
            current_arg += char
        elif not in_string and char == ',':
            args.append(current_arg.strip())
            current_arg = ""
        else:
            current_arg += char
    
    # Add the last argument
    if current_arg.strip():
        args.append(current_arg.strip())
    
    # Clean up arguments (remove quotes from strings, convert numbers)
    cleaned_args = []
    for arg in args:
        arg = arg.strip()
        if arg.startswith('"') and arg.endswith('"'):
            cleaned_args.append(arg[1:-1])  # Remove quotes
        elif arg.startswith("'") and arg.endswith("'"):
            cleaned_args.append(arg[1:-1])  # Remove quotes
        elif arg.isdigit():
            cleaned_args.append(arg)  # Keep as string for consistency
        else:
            cleaned_args.append(arg)
    
    return cleaned_args


def parse_lua_for_depots(lua_path):
    """
    Reads a given .lua file and extracts all DepotID that have a corresponding
    DepotKey, properly distinguishing between the AppID (from filename) and actual DepotID.

    Args:
        lua_path (str or Path): The full path to the .lua file to be parsed.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if the file is not found or an error occurs.
    """
    # Convert to Path object if needed
    lua_path = Path(lua_path)
    logger.debug(f"Parsing lua file for depots: {lua_path}")
    
    # Extract AppID from filename to exclude it from depot results
    app_id = lua_path.stem
    logger.debug(f"AppID from filename: {app_id}")
    
    extracted_depots = []
    try:
        with lua_path.open('r', encoding='utf-8') as f:
            for line_num, raw_line in enumerate(f, 1):
                try:
                    # Preprocess the line
                    line = preprocess_lua_line(raw_line)
                    
                    if not line:
                        continue
                    
                    # Check for adddepot calls
                    args = extract_function_calls(line, 'adddepot')
                    if args and len(args) >= 2:
                        depot_id, depot_key = args[0], args[1]
                        
                        # Validate depot_id is numeric and has a non-empty key
                        if depot_id.isdigit() and depot_key.strip() and depot_id != app_id:
                            extracted_depots.append({
                                'depot_id': depot_id,
                                'depot_key': depot_key
                            })
                            logger.debug(f"Found adddepot: {depot_id} with key")
                            continue
                    
                    # Check for addappid calls with key
                    args = extract_function_calls(line, 'addappid')
                    if args and len(args) >= 3:
                        depot_id, flag, depot_key = args[0], args[1], args[2]
                        
                        # Validate depot_id is numeric and has a non-empty key
                        if (depot_id.isdigit() and depot_key.strip() and depot_id != app_id):
                            extracted_depots.append({
                                'depot_id': depot_id,
                                'depot_key': depot_key
                            })
                            logger.debug(f"Found addappid: {depot_id} with key")
                
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num} in {lua_path.name}: {e}")
                    logger.debug(f"Line parsing exception for line {line_num}:", exc_info=True)
                    continue
                        
    except FileNotFoundError:
        logger.warning(f"Could not find file during parsing: {lua_path}")
    except Exception as e:
        logger.error(f"Failed to read or parse {lua_path.name}: {e}")
        logger.debug(f"File parsing exception for {lua_path.name}:", exc_info=True)

    logger.info(f"Extracted {len(extracted_depots)} depots from {lua_path.name}")
    return extracted_depots


def parse_lua_for_all_depots(lua_path):
    """
    Reads a given .lua file and extracts all DepotID from addappid and adddepot calls,
    properly distinguishing between the AppID (from filename) and actual DepotIDs.
    
    This function uses the filename to determine the AppID and only treats other
    numeric IDs as DepotIDs, providing accurate categorization.

    Args:
        lua_path (str or Path): The full path to the .lua file to be parsed.

    Returns:
        dict: A dictionary with 'app_id' (from filename) and 'depots' (list of depot dicts).
              Returns empty data if the file is not found or an error occurs.
    """
    lua_path = Path(lua_path)
    logger.debug(f"Parsing lua file for all depots: {lua_path}")
    
    # Extract AppID from filename
    app_id = lua_path.stem
    logger.debug(f"AppID from filename: {app_id}")
    
    result = {
        'app_id': app_id,
        'depots': []
    }
    
    # Validate that filename is a numeric AppID
    if not app_id.isdigit():
        logger.warning(f"Filename '{lua_path.name}' does not contain a valid numeric AppID")
        return result

    extracted_depots = []
    try:
        with lua_path.open('r', encoding='utf-8') as f:
            for line_num, raw_line in enumerate(f, 1):
                try:
                    # Preprocess the line
                    line = preprocess_lua_line(raw_line)
                    
                    if not line:
                        continue
                    
                    depot_data = None
                    
                    # Check for adddepot calls
                    args = extract_function_calls(line, 'adddepot')
                    if args and len(args) >= 1:
                        depot_id = args[0]
                        
                        # Skip if this ID matches the AppID (from filename)
                        if depot_id.isdigit() and depot_id != app_id:
                            depot_data = {'depot_id': depot_id}
                            if len(args) >= 2 and args[1].strip():
                                depot_data['depot_key'] = args[1]
                                logger.debug(f"Found adddepot depot {depot_id} with key")
                            else:
                                logger.debug(f"Found adddepot depot {depot_id} without key")
                    
                    # Check for addappid calls
                    if not depot_data:
                        args = extract_function_calls(line, 'addappid')
                        if args and len(args) >= 1:
                            depot_id = args[0]
                            
                            # Skip if this ID matches the AppID (from filename)
                            if depot_id.isdigit() and depot_id != app_id:
                                depot_data = {'depot_id': depot_id}
                                # Check if it has a key (3rd argument)
                                if (len(args) >= 3 and args[2].strip()):
                                    depot_data['depot_key'] = args[2]
                                    logger.debug(f"Found addappid depot {depot_id} with key")
                                else:
                                    logger.debug(f"Found addappid depot {depot_id} without key")
                    
                    # Add or update depot data
                    if depot_data:
                        # Check if we already have this depot
                        existing_depot = next((d for d in extracted_depots 
                                             if d['depot_id'] == depot_data['depot_id']), None)
                        
                        if existing_depot:
                            # Update with key if this entry has one and existing doesn't
                            if 'depot_key' in depot_data and 'depot_key' not in existing_depot:
                                existing_depot['depot_key'] = depot_data['depot_key']
                                logger.debug(f"Updated depot {depot_data['depot_id']} with key")
                        else:
                            # Add new depot
                            extracted_depots.append(depot_data)
                
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num} in {lua_path.name}: {e}")
                    logger.debug(f"Line parsing exception for line {line_num}:", exc_info=True)
                    continue
    
    except FileNotFoundError:
        logger.warning(f"Could not find file during parsing: {lua_path}")
    except Exception as e:
        logger.error(f"Failed to read or parse {lua_path.name}: {e}")
        logger.debug(f"File parsing exception for {lua_path.name}:", exc_info=True)

    result['depots'] = extracted_depots
    logger.info(f"Extracted {len(extracted_depots)} total depots from {lua_path.name}")
    return result


def parse_all_lua_files(data_dir='data'):
    """
    Scans the entire 'data' directory for .lua files and extracts all depot
    information from them.

    Args:
        data_dir (str or Path): The directory to scan for .lua files. Defaults to 'data'.

    Returns:
        list: A list of dictionaries. Each dictionary represents a found depot
              and has the keys 'depot_id' and 'depot_key'. Returns an empty
              list if no data directory is found or no .lua files exist.
    """
    data_dir = Path(data_dir)
    logger.debug(f"Starting to parse all lua files in directory: {data_dir}")
    all_depots = []
    
    if not data_dir.is_dir():
        logger.warning(f"Data directory '{data_dir}' not found")
        return all_depots
    
    lua_files_found = 0
    logger.info(f"Scanning '{data_dir}' directory for .lua files")
    
    # Walk through all subdirectories in the data folder
    for lua_path in data_dir.rglob('*.lua'):
        app_id = lua_path.stem
        logger.debug(f"Processing {lua_path.name} (AppID: {app_id})")
        
        depots = parse_lua_for_depots(lua_path)
        all_depots.extend(depots)
        lua_files_found += 1
    
    logger.info(f"Found {lua_files_found} .lua file(s) containing {len(all_depots)} depot keys total")
    return all_depots


def parse_all_lua_files_structured(data_dir='data'):
    """
    Scans the entire 'data' directory for .lua files and extracts all depot
    information, returning structured data with AppIDs and their associated depots.

    Args:
        data_dir (str or Path): The directory to scan for .lua files. Defaults to 'data'.

    Returns:
        list: A list of dictionaries. Each dictionary has 'app_id' and 'depots' keys.
              Returns empty list if no data directory is found or no .lua files exist.
    """
    # Convert to Path object
    data_dir = Path(data_dir)
    logger.debug(f"Starting structured parsing of all lua files in directory: {data_dir}")
    all_apps = []
    
    if not data_dir.is_dir():
        logger.warning(f"Data directory '{data_dir}' not found")
        return all_apps
    
    lua_files_found = 0
    logger.info(f"Scanning '{data_dir}' directory for .lua files for structured parsing")
    
    # Walk through all subdirectories in the data folder
    for lua_path in data_dir.rglob('*.lua'):
        # Use the improved function that properly categorizes AppID vs DepotID
        app_data = parse_lua_for_all_depots(lua_path)
        
        logger.debug(f"Processing {lua_path.name} (AppID: {app_data['app_id']}) - Found {len(app_data['depots'])} depots")
        
        all_apps.append(app_data)
        lua_files_found += 1
    
    total_depots = sum(len(app['depots']) for app in all_apps)
    logger.info(f"Found {lua_files_found} .lua file(s) containing {total_depots} depot entries total")
    return all_apps


def get_unique_depots(all_depots):
    """
    Remove duplicate depot entries, keeping the last occurrence of each depot ID.

    Args:
        all_depots (list): List of depot dictionaries with 'depot_id' and 'depot_key'.

    Returns:
        dict: Dictionary mapping depot_id to depot_key with duplicates removed.
    """
    unique_depots = {}
    for depot in all_depots:
        unique_depots[depot['depot_id']] = depot['depot_key']
    return unique_depots


# =============================================================================
# --- MAIN EXECUTION ---
# =============================================================================

def main():
    """
    Main function for standalone execution.
    Parses all .lua files and displays the results.
    """
    logger.info("Starting lua_parser.py: Parsing .lua files for depot data")
    
    # Parse command line arguments
    data_dir = Path('data')
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
        logger.debug(f"Using command line data directory: {data_dir}")
    
    # Parse all lua files
    all_depots = parse_all_lua_files(data_dir)
    
    if not all_depots:
        logger.warning("No depot data found")
        return
    
    # Get unique depots
    unique_depots = get_unique_depots(all_depots)
    
    logger.info("Results summary:")
    logger.info(f"Total depot entries: {len(all_depots)}")
    logger.info(f"Unique depot keys: {len(unique_depots)}")
    
    # Display first few entries as sample
    logger.info("Sample depot entries:")
    for i, (depot_id, depot_key) in enumerate(list(unique_depots.items())[:5]):
        logger.info(f"  {depot_id}: {depot_key}")
    
    if len(unique_depots) > 5:
        logger.info(f"  ... and {len(unique_depots) - 5} more")


