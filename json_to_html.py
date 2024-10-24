import json

def json_to_html(json_file, html_file):
    with open(json_file, 'r') as f:
        data = json.load(f)

    html_content = "<html><head><title>Benchmark Results</title></head><body>"
    html_content += "<h1>Benchmark Results</h1>"
    html_content += "<table border='1'><tr><th>Test</th><th>Version</th><th>Mean</th><th>Stddev</th><th>Median</th><th>Min</th><th>Max</th><th>Relative Perf</th></tr>"

    for test, results in data.items():
        for version, metrics in results['summary'].items():
            html_content += f"<tr><td>{test}</td><td>{version}</td>"
            html_content += f"<td>{metrics.get('mean', 'N/A')}</td>"
            html_content += f"<td>{metrics.get('stddev', 'N/A')}</td>"
            html_content += f"<td>{metrics.get('median', 'N/A')}</td>"
            html_content += f"<td>{metrics.get('min', 'N/A')}</td>"
            html_content += f"<td>{metrics.get('max', 'N/A')}</td>"
            html_content += f"<td>{metrics.get('relative_perf', 'N/A')}</td></tr>"

    html_content += "</table></body></html>"

    with open(html_file, 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    json_to_html('benchmark_results.json', 'index.html')
