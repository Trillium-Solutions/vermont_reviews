import http.server
import socketserver
import os
import webbrowser
import urllib.parse
import subprocess
from string import Template

# User Configuration
# Root directory to serve (current folder where script runs)
SERVER_ROOT = "/Users/leslielangley/Documents/versionista"
# Subdirectory to scan for MHTML files
SCAN_SUBDIR = "VT htmls/December_2025"
PORT = 8000
INDEX_FILE = "index.html"

# HTML Template for the Dashboard
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vermont Tracked Website Changes Viewer</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #F0F0F0;
            color: #000;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 4px;
        }

        header {
            margin-bottom: 30px;
            border-bottom: 3px solid #003300;
            padding-bottom: 20px;
        }

        h1 {
            font-size: 2em;
            margin: 0;
            color: #003300;
        }

        p.subtitle {
            color: #666;
            margin: 5px 0 0;
        }

        .instructions-box {
            background-color: #e8f5e9;
            border-left: 5px solid #003300;
            padding: 20px;
            margin-bottom: 30px;
            font-size: 1.05em;
            line-height: 1.6;
            color: #000;
        }

        .instructions-box a {
            color: #003300;
            font-weight: 700;
            text-decoration: underline;
        }

        .search-container {
            margin-bottom: 20px;
        }

        .search-input {
            width: 100%;
            padding: 12px;
            font-size: 1em;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }

        /* Group Styles */
        .agency-group {
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
            background: white;
        }

        .agency-title {
            font-size: 1.25em;
            font-weight: 600;
            color: white;
            background-color: #003300;
            padding: 12px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            user-select: none;
            transition: background-color 0.2s;
        }
        
        .agency-title:hover {
            background-color: #004d00;
        }

        .agency-title::after {
            content: '▼';
            margin-left: auto;
            font-size: 0.8em;
            transition: transform 0.2s;
        }
        
        /* Collapsed State */
        .agency-group.collapsed .agency-title::after {
            transform: rotate(-90deg);
        }

        .file-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            padding: 20px;
            background-color: #fff;
        }

        .agency-group.collapsed .file-list {
            display: none;
        }

        .file-item {
            display: block;
            padding: 10px 15px;
            background-color: #f9f9f9;
            border: 1px solid #eee;
            border-radius: 4px;
            color: #000;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.2s;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .file-item:hover {
            background-color: #e0e0e0;
            color: #003300;
        }
        
        /* Utility for hiding via search */
        .hidden {
            display: none !important;
        }

    </style>
</head>
<body>

    <div class="container">
        <header>
            <h1>Vermont Tracked Website Changes Viewer</h1>
            <p class="subtitle">December 2025 • $count Files</p>
        </header>

        <div class="instructions-box">
            <p style="margin-top:0"><strong>Instructions:</strong></p>
            <ul style="margin-bottom:0; padding-left: 20px;">
                <li>Click an agency name to expand/collapse its files.</li>
                <li>Click an "https link" button to review the changes (the link will open in a new window).</li>
                <li><strong>Important:</strong> If a change needs to be reflected in your <strong>GTFS data feed</strong>, please notify our data technicians. Send an email to <a href="mailto:gtfs.support@optibus.com">gtfs.support@optibus.com</a>,  including the relevant URL(s) and any additional notes on the change(s) you would like us to make.</li>
            </ul>
        </div>

        <div class="search-container">
            <input type="text" class="search-input" placeholder="Filter agencies or files..." onkeyup="filterContent()">
        </div>

        <div id="content-list">
            $file_list
        </div>
    </div>

    <script>
        function openFile(filename) {
            fetch('/open_file?name=' + encodeURIComponent(filename))
                .then(response => {
                    if (response.ok) {
                        console.log('File opened');
                    } else {
                        alert('Error opening file: ' + filename);
                    }
                });
        }

        function toggleGroup(header) {
            header.parentElement.classList.toggle('collapsed');
        }

        function filterContent() {
            const query = document.querySelector('.search-input').value.toLowerCase();
            const items = document.querySelectorAll('.file-item');
            const groups = document.querySelectorAll('.agency-group');

            // Filter items
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(query)) {
                    item.classList.remove('hidden');
                } else {
                    item.classList.add('hidden');
                }
            });

            // Filter Groups
            groups.forEach(group => {
                const title = group.querySelector('.agency-title').textContent.toLowerCase();
                const visibleItems = group.querySelectorAll('.file-item:not(.hidden)');
                const titleMatch = title.includes(query);
                
                if (titleMatch) {
                    // If agency matches, show all its items and uncollapse
                    group.querySelectorAll('.file-item').forEach(i => i.classList.remove('hidden'));
                    group.classList.remove('hidden');
                    group.classList.remove('collapsed');
                } else {
                    if (visibleItems.length > 0) {
                        group.classList.remove('hidden');
                        // Expand if we found items inside
                        group.classList.remove('collapsed');
                    } else {
                        group.classList.add('hidden');
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

def generate_index_html(server_root, scan_subdir):
    """Scans subdirectories and produces the index.html file with flat/grouped structure."""
    
    html_content = ""
    total_files = 0
    full_scan_path = os.path.join(server_root, scan_subdir)
    
    if not os.path.exists(full_scan_path):
        print(f"Error: Scan path not found: {full_scan_path}")
        return 0

    try:
        items = os.listdir(full_scan_path)
        items.sort()
        
        for item in items:
            item_path = os.path.join(full_scan_path, item)
            
            # Case 1: Agency Folder
            if os.path.isdir(item_path):
                folder_name = item.replace("_", " ")
                
                # Start Agency Section (Added onclick toggle)
                group_html = f'<div class="agency-group"><div class="agency-title" onclick="toggleGroup(this)">{folder_name}</div><div class="file-list">'
                
                subfiles = [f for f in os.listdir(item_path) if f.lower().endswith(('.mhtml', '.mht', '.html'))]
                subfiles.sort()
                
                if not subfiles:
                    continue 

                for f in subfiles:
                    display_name = f.replace("Comparison_", "").replace("← Versionista", "").replace(".mhtml", "").replace(".html", "").replace("_"," ")
                    # Construct relative path from SERVER_ROOT to the file
                    # Scan subdir + folder + filename
                    rel_path = os.path.join(scan_subdir, item, f)
                    
                    # File Item with onclick (Removed the explicitly appended newline)
                    group_html += f'<a class="file-item" onclick="openFile(\'{rel_path}\')">{display_name}</a>'
                    total_files += 1
                
                group_html += '</div></div>'
                html_content += group_html

    except Exception as e:
        print(f"Error scanning directory: {e}")

    content = Template(HTML_TEMPLATE).safe_substitute(count=total_files, file_list=html_content)
    
    output_path = os.path.join(server_root, INDEX_FILE)
    with open(output_path, "w") as f:
        f.write(content)
    
    print(f"Generated {INDEX_FILE} in {server_root} with {total_files} files.")
    return total_files

class MHTMLRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for local file launching."""
    def do_GET(self):
        if self.path.startswith('/open_file'):
            try:
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                filename = params.get('name', [None])[0]
                
                if filename:
                    # Security Check: allow relative paths but block traversal
                    if '..' in filename:
                         self.send_error(400, "Invalid filename")
                         return

                    file_path = os.path.join(os.getcwd(), filename)
                    if os.path.exists(file_path):
                        print(f"Opening in Chrome: {file_path}")
                        subprocess.run(['open', '-a', 'Google Chrome', file_path])
                        
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"OK")
                        return
                    else:
                         self.send_error(404, "File not found")
                         return
            except Exception as e:
                print(f"Error handling open request: {e}")
                self.send_error(500, str(e))
                return
        
        return super().do_GET()

def run_server(directory, port):
    """Starts the http server in the target directory."""
    os.chdir(directory)
    handler = MHTMLRequestHandler
    
    print(f"Serving directory: {directory}")

    # Try ports
    while port < 8100:
        try:
            with socketserver.TCPServer(("", port), handler) as httpd:
                print(f"Server started at http://localhost:{port}")
                print("Press Ctrl+C to stop.")
                webbrowser.open(f"http://localhost:{port}")
                httpd.serve_forever()
            break
        except OSError:
            print(f"Port {port} in use, trying {port+1}...")
            port += 1
        except KeyboardInterrupt:
            print("\\nServer stopped.")
            break

if __name__ == "__main__":
    if not os.path.exists(SERVER_ROOT):
        print(f"Error: Directory {SERVER_ROOT} not found.")
    else:
        generate_index_html(SERVER_ROOT, SCAN_SUBDIR)
        run_server(SERVER_ROOT, PORT)
