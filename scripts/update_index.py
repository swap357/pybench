import json
import os
from datetime import datetime

def create_index_page(runs_dir='runs'):
    """Create an index page with links to all benchmark runs"""
    runs = []
    for filename in os.listdir(runs_dir):
        if filename.endswith('.json'):
            with open(os.path.join(runs_dir, filename), 'r') as f:
                data = json.load(f)
                run_id = filename.replace('.json', '')
                timestamp = datetime.fromtimestamp(os.path.getctime(
                    os.path.join(runs_dir, filename)))
                system_info = data['system_info']
                # Extract git information if available
                git_info = data.get('git_info', {})
                runs.append({
                    'id': run_id,
                    'timestamp': timestamp,
                    'system': system_info,
                    'git': git_info
                })

    # Sort runs by timestamp, most recent first
    runs.sort(key=lambda x: x['timestamp'], reverse=True)

    html_content = """
    <html>
    <head>
        <title>Python Benchmark History</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; max-width: 1200px; margin: 0 auto; }
            h1 { color: #333; text-align: center; margin: 40px 0; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f8f9fa; color: #333; font-weight: bold; }
            tr:nth-child(even) { background-color: #f8f9fa; }
            tr:hover { background-color: #f5f5f5; }
            a { color: #0366d6; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .system-info { color: #666; }
            .timestamp { white-space: nowrap; }
            .git-info { font-size: 0.9em; color: #666; }
        </style>
    </head>
    <body>
        <h1>Python Benchmark History</h1>
        <table>
            <tr>
                <th>Date</th>
                <th>System Information</th>
                <th>Git Info</th>
                <th>Results</th>
            </tr>
    """

    for run in runs:
        system_summary = f"""
            <div class="system-info">
                <div>CPU: {run['system']['cpu_count']} cores @ {run['system']['cpu_freq']['current']:.2f} MHz</div>
                <div>Memory: {run['system']['memory_total'] / (1024**3):.2f} GB</div>
                <div>OS: {run['system']['os_info']}</div>
            </div>
        """
        
        git_info = run.get('git', {})
        git_summary = f"""
            <div class="git-info">
                <div>Branch: {git_info.get('branch', 'N/A')}</div>
                <div>Commit: {git_info.get('commit', 'N/A')}</div>
            </div>
        """ if git_info else "N/A"

        html_content += f"""
            <tr>
                <td class="timestamp">{run['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</td>
                <td>{system_summary}</td>
                <td>{git_summary}</td>
                <td><a href="runs/{run['id']}.html">View Results</a></td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open('index.html', 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    create_index_page()
