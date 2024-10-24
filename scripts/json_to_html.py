import json
import plotly.graph_objects as go
import base64
from io import BytesIO
from datetime import datetime
import os
import shutil

def create_benchmark_page(json_file, output_dir, run_id):
    """Create a detailed benchmark page for a specific run"""
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Extract system information
    system_info = data['system_info']
    cpu_count = system_info['cpu_count']
    memory_total = system_info['memory_total']
    os_info = system_info['os_info']
    cpu_freq = system_info['cpu_freq']
    load_avg = system_info['load_avg']

    html_content = f"""
    <html>
    <head>
        <title>Benchmark Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; max-width: 1400px; margin: 0 auto; }}
            h1, h2 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f8f9fa; color: #333; font-weight: bold; }}
            tr.header {{ background-color: #f8f9fa; font-weight: bold; }}
            tr.baseline {{ background-color: #f8f9fa; }}
            img {{ display: block; margin: 0 auto; max-width: 100%; height: auto; }}
            .system-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .system-info li {{ margin-bottom: 5px; }}
            .flex-container {{ display: flex; justify-content: space-between; flex-wrap: wrap; gap: 20px; }}
            .flex-item {{ flex: 1; min-width: 600px; }}
            .timestamp {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <h1>Benchmark Results</h1>
        <div class="timestamp">Run ID: {run_id}</div>
        <h2>System Information</h2>
        <div class="system-info">
            <ul>
                <li><strong>CPU Count:</strong> {cpu_count}</li>
                <li><strong>Total Memory:</strong> {memory_total / (1024**3):.2f} GB</li>
                <li><strong>OS:</strong> {os_info}</li>
                <li><strong>CPU Frequency:</strong> {cpu_freq['current']:.2f} MHz</li>
                <li><strong>Load Average:</strong> [{', '.join(f'{x:.2f}' for x in load_avg)}]</li>
            </ul>
        </div>
        <div class="flex-container">
    """

    # Prepare data for the plots
    test_names = []
    version_data = {}

    for test_name, test_data in data['benchmarks'].items():
        test_names.append(test_name)
        for version, metrics in test_data['summary'].items():
            if version not in version_data:
                version_data[version] = {'medians': [], 'stddevs': [], 'relative_perfs': []}
            version_data[version]['medians'].append(metrics['median'])
            version_data[version]['stddevs'].append(metrics['stddev'])
            relative_perf = 100 if metrics.get('relative_perf') is None else float(metrics['relative_perf'].strip('%'))
            version_data[version]['relative_perfs'].append(relative_perf)

    # Create plots
    colors = ['#757575', '#64b5f6', '#ffb74d']  # Grey for baseline
    sorted_versions = ['3.12.7', '3.13.0', '3.13.0t']

    # Execution time comparison plot
    fig1 = go.Figure()
    for idx, version in enumerate(sorted_versions):
        metrics = version_data[version]
        fig1.add_trace(go.Bar(
            name=version,
            y=test_names,
            x=metrics['relative_perfs'],
            orientation='h',
            marker_color=colors[idx % len(colors)]
        ))

    fig1.update_layout(
        title="Execution Time Comparison Across Tests",
        xaxis_title="Execution Time Increase (%)",
        yaxis_title="Benchmark Test",
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=600
    )

    # Median execution time plot
    fig2 = go.Figure()
    for idx, version in enumerate(sorted_versions):
        metrics = version_data[version]
        fig2.add_trace(go.Bar(
            name=version,
            y=test_names,
            x=metrics['medians'],
            error_x=dict(type='data', array=metrics['stddevs']),
            orientation='h',
            marker_color=colors[idx % len(colors)]
        ))

    fig2.update_layout(
        title="Median Execution Time with Error Bars",
        xaxis_title="Median Execution Time (s)",
        yaxis_title="Benchmark Test",
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=600
    )

    # Add plots to HTML
    img_bytes1 = fig1.to_image(format="png")
    img_bytes2 = fig2.to_image(format="png")
    html_content += f'''
        <div class="flex-item"><img src="data:image/png;base64,{base64.b64encode(img_bytes1).decode('utf-8')}" alt="Performance Comparison"/></div>
        <div class="flex-item"><img src="data:image/png;base64,{base64.b64encode(img_bytes2).decode('utf-8')}" alt="Execution Time with Error Bars"/></div>
    </div>
    '''

    # Add detailed statistics table
    html_content += "<h2>Detailed Statistics</h2><table>"

    for test_name, test_data in data['benchmarks'].items():
        html_content += f"""
        <tr class="header">
            <td colspan="7">{test_name}</td>
        </tr>
        <tr>
            <th>Python Version</th>
            <th>Median</th>
            <th>Stddev</th>
            <th>Mean</th>
            <th>Min</th>
            <th>Max</th>
            <th>Execution Time Increase</th>
        </tr>
        """
        for version, metrics in test_data['summary'].items():
            row_class = "baseline" if metrics.get('relative_perf') is None else ""
            relative_perf = 100 if metrics.get('relative_perf') is None else float(metrics['relative_perf'].strip('%'))
            html_content += f"""
            <tr class="{row_class}">
                <td>{version}</td>
                <td>{metrics['median']:.4f}</td>
                <td>{metrics['stddev']:.4f}</td>
                <td>{metrics['mean']:.4f}</td>
                <td>{metrics['min']:.4f}</td>
                <td>{metrics['max']:.4f}</td>
                <td>{relative_perf:.2f}%</td>
            </tr>
            """

    html_content += "</table></body></html>"

    output_file = os.path.join(output_dir, f"{run_id}.html")
    with open(output_file, 'w') as f:
        f.write(html_content)

def json_to_html(json_file):
    """Process benchmark results and create a single run page"""
    runs_dir = 'runs'
    os.makedirs(runs_dir, exist_ok=True)

    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(json_file, os.path.join(runs_dir, f"{run_id}.json"))
    create_benchmark_page(json_file, runs_dir, run_id)
    return run_id

if __name__ == "__main__":
    json_to_html('benchmark_report.json')
