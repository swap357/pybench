import json
import plotly.graph_objects as go
import base64
from io import BytesIO

def json_to_html(json_file, html_file):
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
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #b0bec5; color: #333; }}
            tr.header {{ background-color: #eceff1; font-weight: bold; }}
            tr.baseline {{ background-color: #cfd8dc; }}
            img {{ display: block; margin: 0 auto; }}
            .system-info {{ background-color: #f7f7f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .system-info li {{ margin-bottom: 5px; }}
            .flex-container {{ display: flex; justify-content: space-around; flex-wrap: wrap; }}
            .flex-item {{ flex: 1; min-width: 300px; margin: 10px; }}
        </style>
    </head>
    <body>
        <h1>Benchmark Results</h1>
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

    # Prepare data for the plot
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

    # Create a horizontal bar chart for execution time increase
    fig = go.Figure()
    colors = ['#757575', '#64b5f6', '#ffb74d']

    sorted_versions = ['3.12.7', '3.13.0', '3.13.0t']

    for idx, version in enumerate(sorted_versions):
        metrics = version_data[version]
        fig.add_trace(go.Bar(
            name=version,
            y=test_names,
            x=metrics['relative_perfs'],
            orientation='h',
            marker_color=colors[idx % len(colors)]
        ))

    fig.update_layout(
        title="Execution Time Comparison Across Tests",
        xaxis_title="Execution Time Increase (%)",
        yaxis_title="Benchmark Test",
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Convert plot to image and embed in HTML
    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    html_content += f'<div class="flex-item"><img src="data:image/png;base64,{img_base64}" alt="Performance Comparison"/></div>'

    # Add horizontal bar chart with error bars
    fig_error = go.Figure()

    for idx, version in enumerate(sorted_versions):
        metrics = version_data[version]
        fig_error.add_trace(go.Bar(
            name=version,
            y=test_names,
            x=metrics['medians'],
            error_x=dict(type='data', array=metrics['stddevs']),
            orientation='h',
            marker_color=colors[idx % len(colors)]
        ))

    fig_error.update_layout(
        title="Median Execution Time with Error Bars",
        xaxis_title="Median Execution Time (s)",
        yaxis_title="Benchmark Test",
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Convert error bar plot to image and embed in HTML
    img_bytes_error = fig_error.to_image(format="png")
    img_base64_error = base64.b64encode(img_bytes_error).decode('utf-8')
    html_content += f'<div class="flex-item"><img src="data:image/png;base64,{img_base64_error}" alt="Execution Time with Error Bars"/></div>'

    html_content += "</div>"

    # Add table with raw numbers
    html_content += "<h2>Detailed Statistics</h2>"
    html_content += "<table>"

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
            median = metrics['median']
            stddev = metrics['stddev']
            mean = metrics['mean']
            min_val = metrics['min']
            max_val = metrics['max']
            relative_perf = 100 if metrics.get('relative_perf') is None else float(metrics['relative_perf'].strip('%'))

            row_class = "baseline" if metrics.get('relative_perf') is None else ""
            html_content += f"""
            <tr class="{row_class}">
                <td>{version}</td>
                <td>{median:.4f}</td>
                <td>{stddev:.4f}</td>
                <td>{mean:.4f}</td>
                <td>{min_val:.4f}</td>
                <td>{max_val:.4f}</td>
                <td>{relative_perf:.2f}%</td>
            </tr>
            """

    html_content += "</table></body></html>"

    with open(html_file, 'w') as f:
        f.write(html_content)

if __name__ == "__main__":
    json_to_html('benchmark_report.json', 'index.html')
