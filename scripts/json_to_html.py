import json
import plotly.graph_objects as go
import base64
from io import BytesIO
from datetime import datetime
import os
import shutil
import argparse
import colorsys
import re

def get_version_colors(versions_info):
    """Generate colors for different versions"""
    # Fixed color for baseline
    colors = {'baseline': '#757575'}  # Grey for baseline
    
    # Modern, pastel-like color palette for major versions
    major_version_base_colors = [
        '#6b9bd0',  # Soft Blue
        '#e6b566',  # Warm Sand
        '#6ec1c5',  # Seafoam
        '#d6876f',  # Muted Coral
        '#86b985',  # Sage Green
        '#e28cb9',  # Dusty Rose
        '#e28cb9',  # Dusty Rose
        '#b7c06e',  # Olive Green
        '#c76b6b',  # Faded Red
        '#7c98b3',  # Steel Blue
    ]
    
    def adjust_color(hex_color, darkness):
        # darkness should be between 0 (lightest) and 1 (darkest)
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])
        l = 1 - (darkness * 0.5)  # Adjust lightness, keeping it between 0.5 and 1
        rgb = colorsys.hls_to_rgb(h, l, s)
        return f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
    
    def get_version_number(version):
        match = re.match(r'(\d+)([a-z]*)', version)
        if match:
            num, suffix = match.groups()
            return int(num), suffix
        return 0, ''
    
    # Group versions by major version
    major_version_groups = {}
    for version in versions_info.get('metadata', {}):
        major_version = '.'.join(version.split('.')[:2])
        if major_version not in major_version_groups:
            major_version_groups[major_version] = []
        major_version_groups[major_version].append(version)
    
    # Assign colors to versions
    for i, (major_version, versions) in enumerate(major_version_groups.items()):
        base_color = major_version_base_colors[i % len(major_version_base_colors)]
        
        # Sort versions within major version
        sorted_versions = sorted(versions, key=lambda v: (v.split('.')[2], v))
        num_versions = len(sorted_versions)
        
        for j, version in enumerate(sorted_versions):
            version_type = versions_info['metadata'][version].get('type')
            if version_type == 'baseline':
                continue
            
            # Calculate darkness based on position
            if num_versions == 1:
                darkness = 1.0  # Darkest for single version
            elif num_versions == 2:
                darkness = 1.0 if j == 0 else 0.4  # 10 and 4 on a scale of 1-10
            else:
                darkness = 1 - (j / (num_versions - 1))  # Spread evenly across spectrum, reversed
            
            colors[version] = adjust_color(base_color, darkness)
    
    return colors

def create_benchmark_page(json_file, output_dir, run_id):
    """Create a detailed benchmark page for a specific run"""
    with open(json_file, 'r') as f:
        data = json.load(f)
        
    # Get versions info from the results
    versions_info = data['results'].get('versions_info', {})
    
    # Get actual versions from the first benchmark's results
    # Try regular tests first, then scaling tests
    first_benchmark = None
    if data['results'].get('regular_tests'):
        first_benchmark = next(iter(data['results']['regular_tests'].values()))
    elif data['results'].get('scaling_tests'):
        first_benchmark = next(iter(data['results']['scaling_tests'].values()))
    
    if not first_benchmark:
        print("No benchmark results found")
        return
        
    actual_versions = list(first_benchmark.keys())
    sorted_versions = sorted(actual_versions, 
                           key=lambda v: (v != versions_info.get('baseline', '3.12.7'), v), 
                           reverse=True)
    baseline_version = versions_info.get('baseline', '3.12.7')

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
        <title>Benchmark results: {run_id}</title>
        <script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; max-width: 1400px; margin: 0 auto; }}
            h1, h2 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f8f9fa; color: #333; font-weight: bold; }}
            tr.header {{ background-color: #f8f9fa; font-weight: bold; }}
            tr.baseline {{ background-color: #f8f9fa; }}
            .system-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .system-info li {{ margin-bottom: 5px; }}
            .plot-container {{ margin: 30px 0; }}
            .timestamp {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
            .breadcrumb {{ 
                padding: 10px 0;
                margin-bottom: 20px;
                border-bottom: 1px solid #eee;
            }}
            .breadcrumb a {{ 
                color: #0366d6;
                text-decoration: none;
            }}
            .breadcrumb a:hover {{ 
                text-decoration: underline;
            }}
            .breadcrumb span {{ 
                color: #666;
                margin: 0 5px;
            }}
            .info-section {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .info-section h2 {{
                margin-top: 0;
            }}
            .info-section li {{
                margin-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="breadcrumb">
            <a href="../../index.html">← Back to index</a>
        </div>
        <h1>Benchmark Results</h1>
        
        <div class="info-section">
            <h2>Run Configuration</h2>
            <ul>
                <li><strong>Run ID:</strong> {run_id}</li>
                <li><strong>Iterations:</strong> {data['run_config']['iterations']}</li>
                <li><strong>Thread Config:</strong> {data['run_config']['threads']}</li>
                <li><strong>Category:</strong> {data['run_config']['category']}</li>
            </ul>
        </div>

        <div class="info-section">
            <h2>System Information</h2>
            <ul>
                <li><strong>CPU Count:</strong> {cpu_count}</li>
                <li><strong>CPU Affinity:</strong> {system_info.get('cpu_affinity', 'Not restricted')}</li>
                <li><strong>Total Memory:</strong> {memory_total / (1024**3):.2f} GB</li>
                <li><strong>OS:</strong> {os_info}</li>
                <li><strong>CPU Frequency:</strong> {cpu_freq['current']:.2f} MHz</li>
                <li><strong>Load Average:</strong> [{', '.join(f'{x:.2f}' for x in load_avg)}]</li>
            </ul>
        </div>

    """

    # Prepare data for the plots
    test_names = []
    version_data = {}

    # Process regular test results
    regular_tests = data['results'].get('regular_tests', {})
    for test_name, test_data in regular_tests.items():
        test_names.append(test_name)
        for version, metrics in test_data.items():
            if version not in version_data:
                version_data[version] = {'medians': [], 'stddevs': [], 'relative_perfs': []}
            
            stats = metrics.get('statistical_data', {})
            version_data[version]['medians'].append(stats.get('median', 0))
            version_data[version]['stddevs'].append(stats.get('stddev', 0))
            
            relative_perf = 100
            if metrics.get('relative_performance'):
                relative_perf = float(metrics['relative_performance'].strip('%'))
            version_data[version]['relative_perfs'].append(relative_perf)

    # Process scaling test results
    scaling_tests = data['results'].get('scaling_tests', {})
    for test_name, test_data in scaling_tests.items():
        test_names.append(test_name)
        for version, metrics in test_data.items():
            if version not in version_data:
                version_data[version] = {'medians': [], 'stddevs': [], 'relative_perfs': []}
            
            stats = metrics.get('statistical_data', {})
            version_data[version]['medians'].append(stats.get('median', 0))
            version_data[version]['stddevs'].append(stats.get('stddev', 0))
            
            relative_perf = 100
            if metrics.get('relative_performance'):
                relative_perf = float(metrics['relative_performance'].strip('%'))
            version_data[version]['relative_perfs'].append(relative_perf)

    # Get versions info and generate colors
    versions_info = data['results'].get('versions_info', {})
    colors = get_version_colors(versions_info)

    # Create plot data for execution time comparison
    perf_comparison_data = []
    
    for version in sorted_versions:
        metrics = version_data[version]
        color = colors.get(version, '#757575')
        perf_comparison_data.append({
            'type': 'bar',
            'name': version,
            'x': metrics['relative_perfs'],
            'y': test_names,
            'orientation': 'h',
            'marker': {'color': color}
        })

    perf_comparison_layout = {
        'title': 'Execution Time Comparison Across Tests',
        'xaxis': {'title': 'Execution Time Increase (%)'},
        'yaxis': {
            'title': '',
            'automargin': True,  # Automatically adjust margin for labels
            'tickfont': {'size': 11}  # Adjust font size if needed
        },
        'barmode': 'group',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'height': 800,
        'margin': {
            'l': 300,  # Increased left margin
            't': 50,   # Top margin
            'b': 50,   # Bottom margin
            'r': 50,   # Right margin
            'pad': 4   # Padding between axis and labels
        }
    }

    # Create plot data for median execution time
    exec_time_data = []
    for version in sorted_versions:
        metrics = version_data[version]
        color = colors.get(version, '#757575')
        exec_time_data.append({
            'type': 'bar',
            'name': version,
            'x': metrics['medians'],
            'y': test_names,
            'orientation': 'h',
            'error_x': {
                'type': 'data',
                'array': metrics['stddevs'],
                'visible': True
            },
            'marker': {'color': color}
        })

    exec_time_layout = {
        'title': 'Median Execution Time with Error Bars',
        'xaxis': {'title': 'Median Execution Time (s)'},
        'yaxis': {
            'title': '',
            'automargin': True,  # Automatically adjust margin for labels
            'tickfont': {'size': 11}  # Adjust font size if needed
        },
        'barmode': 'group',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'height': 800,
        'margin': {
            'l': 300,  # Increased left margin
            't': 50,   # Top margin
            'b': 50,   # Bottom margin
            'r': 50,   # Right margin
            'pad': 4   # Padding between axis and labels
        }
    }

    # Add regular plots
    html_content += """
        <div class="plot-container">
            <div id="perf_comparison" style="width:100%;height:800px;"></div>
        </div>
        <div class="plot-container">
            <div id="exec_time" style="width:100%;height:800px;"></div>
        </div>
    """

    # Add scaling test plots
    if scaling_tests:
        html_content += "<h2>Scaling Test Plots</h2>"
        for i, (test_name, test_data) in enumerate(scaling_tests.items()):
            html_content += f"""
            <div class="plot-container">
                <div id="scaling_plot_{i}" style="width:100%;height:600px;"></div>
            </div>
            """
            
            # Add bandwidth plot for memory bandwidth tests
            if "memory_bandwidth" in test_name:
                html_content += f"""
                <div class="plot-container">
                    <div id="bandwidth_plot_{i}" style="width:100%;height:600px;"></div>
                </div>
                """

    # Add plot initialization scripts
    html_content += f"""
        <script>
            const perfComparisonData = {json.dumps(perf_comparison_data)};
            const perfComparisonLayout = {json.dumps(perf_comparison_layout)};
            Plotly.newPlot('perf_comparison', perfComparisonData, perfComparisonLayout);

            const execTimeData = {json.dumps(exec_time_data)};
            const execTimeLayout = {json.dumps(exec_time_layout)};
            Plotly.newPlot('exec_time', execTimeData, execTimeLayout);
    """

    # Add scaling plot initialization
    for i, (test_name, test_data) in enumerate(scaling_tests.items()):
        plot_data, layout = create_scaling_plots(test_name, test_data, versions_info, colors)
        html_content += f"""
            const scalingData_{i} = {json.dumps(plot_data)};
            const scalingLayout_{i} = {json.dumps(layout)};
            Plotly.newPlot('scaling_plot_{i}', scalingData_{i}, scalingLayout_{i});
        """
        
        # Add bandwidth plot initialization for memory bandwidth tests
        if "memory_bandwidth" in test_name:
            bw_data, bw_layout = create_bandwidth_plot(test_name, test_data, versions_info, colors)
            html_content += f"""
                const bandwidthData_{i} = {json.dumps(bw_data)};
                const bandwidthLayout_{i} = {json.dumps(bw_layout)};
                Plotly.newPlot('bandwidth_plot_{i}', bandwidthData_{i}, bandwidthLayout_{i});
            """

    html_content += "</script>"

    # Add detailed statistics table
    html_content += "<h2>Statistics</h2><table>"

    # Add regular test statistics
    if regular_tests:
        html_content += "<h2>Regular Test Statistics</h2><table>"
        for test_name, test_data in regular_tests.items():
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
            html_content += _add_test_statistics(html_content, test_data)
        html_content += "</table>"

    # Add scaling test statistics
    if scaling_tests:
        html_content += "<h2>Scaling Test Statistics</h2><table>"
        for test_name, test_data in scaling_tests.items():
            html_content += f"""
            <tr class="header">
                <td colspan="6">{test_name}</td>
            </tr>
            <tr>
                <th>Python Version</th>
                <th>Base Duration</th>
                <th>Max Speedup</th>
                <th>Efficiency</th>
                <th>Max Threads</th>
                <th>Relative Performance</th>
            </tr>
            """
            html_content += _add_scaling_test_statistics(html_content, test_data)
        html_content += "</table>"

    html_content += "</body></html>"

    # Write the file
    output_file = os.path.join(output_dir, "results.html")
    with open(output_file, 'w') as f:
        f.write(html_content)

def _add_test_statistics(html_content: str, test_data: dict) -> str:
    """Helper function to add test statistics rows"""
    table_rows = ""
    for version, metrics in test_data.items():
        stats = metrics['statistical_data']
        row_class = "baseline" if metrics.get('relative_performance') is None else ""
        relative_perf = 100 if metrics.get('relative_performance') is None else float(metrics['relative_performance'].strip('%'))
        table_rows += f"""
        <tr class="{row_class}">
            <td>{version}</td>
            <td>{stats['median']:.4f}</td>
            <td>{stats['stddev']:.4f}</td>
            <td>{stats['mean']:.4f}</td>
            <td>{stats['min']:.4f}</td>
            <td>{stats['max']:.4f}</td>
            <td>{relative_perf:.2f}%</td>
        </tr>
        """
    return table_rows

def _add_scaling_test_statistics(html_content: str, test_data: dict) -> str:
    """Helper function to add scaling test statistics rows"""
    table_rows = ""
    for version, metrics in test_data.items():
        stats = metrics['statistical_data']
        row_class = "baseline" if metrics.get('relative_performance') is None else ""
        relative_perf = 100 if metrics.get('relative_performance') is None else float(metrics['relative_performance'].strip('%'))
        table_rows += f"""
        <tr class="{row_class}">
            <td>{version}</td>
            <td>{stats['median']:.4f}</td>
            <td>{metrics['scaling_factor']:.2f}x</td>
            <td>{metrics['efficiency']:.2%}</td>
            <td>{metrics['max_threads']}</td>
            <td>{relative_perf:.2f}%</td>
        </tr>
        """
    return table_rows

def create_scaling_plots(test_name: str, test_data: dict, versions_info: dict, colors: dict) -> tuple:
    """Create scaling plots for a specific test."""
    # Get all available metrics from first test's data
    first_version = next(iter(test_data.values()))
    first_scaling_point = first_version['scaling_data'][0]  # Direct access to scaling point
    
    # Get all metrics excluding standard fields
    standard_fields = {'thread_count', 'duration', 'speedup', 'iterations_per_thread'}
    
    # Get metrics from the 'metrics' dictionary
    metrics = ['speedup'] + list(first_scaling_point['metrics'].keys())
    
    # Create traces for each version and metric
    plot_data = []
    for version in test_data.keys():
        # Get the scaling data points directly
        scaling_points = test_data[version]['scaling_data']
        x = [point['thread_count'] for point in scaling_points]
        
        # Create trace for speedup
        y = [point['speedup'] for point in scaling_points]
        plot_data.append({
            'type': 'scatter',
            'name': f"{version}",
            'x': x,
            'y': y,
            'line': {'color': colors.get(version, '#757575')}
        })

    layout = {
        'title': f'{test_name} - Speedup vs Thread Count',
        'xaxis': {'title': 'Thread Count'},
        'yaxis': {'title': 'Speedup'},
        'showlegend': True,
        'height': 600
    }

    return plot_data, layout

def create_bandwidth_plot(test_name: str, test_data: dict, versions_info: dict, colors: dict) -> tuple:
    """Create bandwidth plot for memory bandwidth tests."""
    plot_data = []
    
    # Get unique thread counts across all versions
    thread_counts = sorted(set(
        point['thread_count'] 
        for version_data in test_data.values() 
        for point in version_data['scaling_data']
    ))
    
    for version in test_data.keys():
        # Get the scaling data points directly
        scaling_points = test_data[version]['scaling_data']
        x = [point['thread_count'] for point in scaling_points]
        
        # Get bandwidth data
        y = [point['metrics']['bandwidth_MB_s'] for point in scaling_points]
        
        plot_data.append({
            'type': 'scatter',
            'name': f"{version}",
            'x': x,
            'y': y,
            'line': {'color': colors.get(version, '#757575')}
        })

    layout = {
        'title': f'{test_name} - Memory Bandwidth vs Thread Count',
        'xaxis': {
            'title': 'Thread Count',
            'type': 'log',
            'tickmode': 'array',
            'tickvals': thread_counts,
            'ticktext': [str(t) for t in thread_counts]
        },
        'yaxis': {'title': 'Bandwidth (MB/s)'},
        'showlegend': True,
        'height': 600,
        'grid': {'pattern': 'independent'}
    }

    return plot_data, layout

def json_to_html(json_file, output_dir='runs', run_id=None):
    """Process benchmark results and create a single run page"""
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # No directory creation here, just create the page
    create_benchmark_page(json_file, output_dir, run_id)
    return run_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate HTML report from benchmark results')
    parser.add_argument('--input-file', default='benchmark_results.json', help='Input JSON file')
    parser.add_argument('--output-dir', default='runs', help='Output directory for HTML report')
    parser.add_argument('--run-id', help='Run ID (timestamp) for this benchmark run')
    args = parser.parse_args()
    
    json_to_html(args.input_file, args.output_dir, args.run_id)

