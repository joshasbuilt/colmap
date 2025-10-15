# HAR Files Directory

Place your HAR files in this directory for processing.

## How to Capture HAR Files from Web Browsers

### Chrome/Edge
1. Open Chrome or Edge browser
2. Press `F12` or right-click → "Inspect" to open Developer Tools
3. Go to the **Network** tab
4. Check the "Preserve log" checkbox (important!)
5. Clear the network log (click the clear button 🚫)
6. Navigate to the website you want to capture
7. Perform the actions you want to record
8. Right-click in the Network tab → "Save all as HAR with content"
9. Save the file with a descriptive name (e.g., `website_analysis.har`)

### Firefox
1. Open Firefox browser
2. Press `F12` or right-click → "Inspect Element" → "Network" tab
3. Check "Persist Logs" checkbox
4. Clear the network log
5. Navigate to the website and perform actions
6. Right-click in the Network tab → "Save All As HAR"
7. Save the file with a descriptive name

### Safari
1. Enable Developer menu: Safari → Preferences → Advanced → "Show Develop menu"
2. Open Develop → Show Web Inspector
3. Go to Network tab
4. Navigate to the website and perform actions
5. Right-click in Network tab → "Export HAR"
6. Save the file

### Tips for Better HAR Files
- **Clear the log** before starting your session
- **Enable "Preserve log"** to keep all requests
- **Perform all actions** you want to analyze in one session
- **Use descriptive filenames** (e.g., `login_flow.har`, `api_calls.har`)
- **Include the full user journey** from start to finish

## Supported Formats
- `.har` - Standard HAR files
- `.har.gz` - Compressed HAR files

## Usage
After placing HAR files here, run:
```bash
python process_har_files.py --input-dir har_files --output-dir analysis_output --combine
```

## File Organization
- Place all HAR files directly in this directory
- The processor will automatically detect and process all HAR files
- Results will be saved to the specified output directory
