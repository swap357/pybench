import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re
import argparse

def extract_existing_runs(html_file):
    """Extract existing run information from current index.html"""
    if not os.path.exists(html_file):
        return []
    
    with open(html_file, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    runs = []
    for row in soup.find_all('tr')[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) >= 4:
            run_id = re.search(r'runs/(\d+)/results.html', cols[3].find('a')['href']).group(1)
            runs.append({
                'timestamp': cols[0].text.strip(),
                'system_info': cols[1].text.strip(),
                'git_info': cols[2].text.strip(),
                'id': run_id
            })
    return runs

def get_cpu_freq_display(cpu_freq):
    """Get displayable CPU frequency string"""
    if isinstance(cpu_freq, dict):
        if 'current' in cpu_freq and cpu_freq['current'] not in ['N/A', None]:
            return f"@ {cpu_freq['current']:.2f} MHz"
        # Try to get any available frequency info
        freq_values = [v for v in cpu_freq.values() if v not in ['N/A', None]]
        if freq_values:
            return f"@ {freq_values[0]:.2f} MHz"
    return ""  # Return empty string if no valid frequency found

def update_index_page(json_file='benchmark_results.json', index_file='index.html', run_id=None):
    """Update index.html with new benchmark run"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    timestamp = datetime.now()
    system_info = data['system_info']
    git_info = data.get('git_info', {})
    if run_id:
        timestamp = datetime.strptime(run_id, '%Y%m%d_%H%M%S')
        run_id = run_id
    else:
        run_id = timestamp.strftime('%Y%m%d_%H%M%S')

    # Create new index.html if it doesn't exist
    if not os.path.exists(index_file):
        html_content = """
        <html>
        <head>
            <title>python free-threading benchmarks</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; max-width: 1400px; margin: 0 auto; }
                h1, h2 { color: #333; }
                .header { margin-bottom: 30px; }
                .repo-link { 
                    display: inline-block;
                    margin: 10px 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    color: #0366d6;
                    text-decoration: none;
                }
                .repo-link:hover {
                    background-color: #e9ecef;
                }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f8f9fa; }
                .system-info, .git-info { white-space: pre-line; }
                .timestamp { white-space: nowrap; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>python free-threading benchmarks</h1>
                <a href="https://github.com/swap357/pybench/" class="repo-link">to GitHub</a>
            </div>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>System Info</th>
                    <th>Git Info</th>
                    <th>Results</th>
                </tr>
            </table>
        </body>
        </html>
        """
        with open(index_file, 'w') as f:
            f.write(html_content)

    # Read existing index.html
    with open(index_file, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Find the table
    table = soup.find('table')
    
    # Create new row
    new_row = soup.new_tag('tr')
    
    # Add timestamp
    td_time = soup.new_tag('td')
    td_time['class'] = 'timestamp'
    td_time.string = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    new_row.append(td_time)
    
    # Add system info with graceful CPU frequency handling
    td_sys = soup.new_tag('td')
    sys_div = soup.new_tag('div')
    sys_div['class'] = 'system-info'
    
    # CPU info with graceful frequency handling
    cpu_freq_str = get_cpu_freq_display(system_info['cpu_freq'])
    sys_div.append(f"CPU: {system_info['cpu_count']} cores {cpu_freq_str}\n")
    sys_div.append(soup.new_tag('br'))
    
    # Rest of system info
    sys_div.append(f"Memory: {system_info['memory_total'] / (1024**3):.2f} GB\n")
    sys_div.append(soup.new_tag('br'))
    sys_div.append(f"OS: {system_info['os_info']}")
    td_sys.append(sys_div)
    new_row.append(td_sys)
    
    # Add git info
    td_git = soup.new_tag('td')
    if git_info:
        git_div = soup.new_tag('div')
        git_div['class'] = 'git-info'
        git_div.append(f"Branch: {git_info.get('branch', 'N/A')}\n")
        git_div.append(soup.new_tag('br'))
        git_div.append(f"Commit: {git_info.get('commit', 'N/A')}")
        td_git.append(git_div)
    else:
        td_git.string = 'N/A'
    new_row.append(td_git)
    
    # Add results link
    td_link = soup.new_tag('td')
    a = soup.new_tag('a', href=f"runs/{run_id}/results.html")
    a.string = 'View Results'
    td_link.append(a)
    new_row.append(td_link)
    
    # Insert new row after header
    header_row = table.find('tr')
    header_row.insert_after(new_row)
    
    # Write updated index.html
    with open(index_file, 'w') as f:
        f.write(str(soup))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update index page with new benchmark results')
    parser.add_argument('--input-file', default='benchmark_results.json', help='Input JSON file')
    parser.add_argument('--index-file', default='index.html', help='Index HTML file to update')
    parser.add_argument('--run-id', help='Run ID (timestamp) for this benchmark run')
    args = parser.parse_args()
    
    update_index_page(args.input_file, args.index_file, args.run_id)
