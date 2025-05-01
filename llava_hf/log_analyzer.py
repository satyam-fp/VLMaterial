#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 Massachusetts Institute of Technology
# See the LICENSE file for full license details.

import os
import os.path as osp
import json
import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict, Counter

def parse_logs(log_path):
    """Parse log files and extract structured data."""
    if not osp.exists(log_path):
        raise FileNotFoundError(f"Log file {log_path} not found")
    
    log_data = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Try to parse as JSON (from log_event function)
                entry = json.loads(line)
                log_data.append(entry)
            except json.JSONDecodeError:
                # Simple log line (from log_info function)
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_data.append({
                    'timestamp': timestamp,
                    'event_type': 'UNKNOWN',
                    'step': 'UNKNOWN',
                    'message': line
                })
    
    return log_data

def analyze_generation_times(log_data):
    """Analyze generation times from log data."""
    generation_times = []
    current_gen = None
    
    for entry in log_data:
        if entry['event_type'] == 'GENERATION' and entry['step'] == 'START':
            current_gen = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
        elif entry['event_type'] == 'GENERATION' and entry['step'] == 'COMPLETE' and current_gen:
            end_time = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            duration = (end_time - current_gen).total_seconds()
            generation_times.append(duration)
            current_gen = None
    
    return generation_times

def analyze_render_times(log_data):
    """Analyze rendering times from log data."""
    render_times = []
    current_render = None
    
    for entry in log_data:
        if entry['event_type'] == 'RENDER' and entry['step'] == 'START':
            current_render = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
        elif entry['event_type'] == 'VERIFY' and entry['step'] == 'SUCCESS' and current_render:
            end_time = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            duration = (end_time - current_render).total_seconds()
            render_times.append(duration)
            current_render = None
        elif entry['event_type'] == 'RENDER' and entry['step'] == 'ERROR' and current_render:
            end_time = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            duration = (end_time - current_render).total_seconds()
            render_times.append(duration)
            current_render = None
    
    return render_times

def analyze_error_types(log_data):
    """Analyze types of errors that occurred."""
    error_counter = Counter()
    
    for entry in log_data:
        if entry['step'] == 'ERROR':
            if 'metadata' in entry and 'error_type' in entry['metadata']:
                error_counter[entry['metadata']['error_type']] += 1
            else:
                error_counter['unknown'] += 1
    
    return error_counter

def analyze_success_rates(log_data):
    """Analyze success rates for each sample."""
    samples = defaultdict(lambda: {'attempted': 0, 'passed': 0})
    
    for entry in log_data:
        if entry['event_type'] == 'VERIFICATION':
            if 'message' in entry and 'Sample' in entry['message']:
                sample_id = entry['message'].split('Sample')[1].split(' ')[1]
                
                if entry['step'] == 'PASSED':
                    samples[sample_id]['passed'] += 1
                if entry['step'] in ['PASSED', 'FAILED']:
                    samples[sample_id]['attempted'] += 1
    
    success_rates = {
        sample_id: data['passed'] / data['attempted'] if data['attempted'] > 0 else 0
        for sample_id, data in samples.items()
    }
    
    return success_rates

def plot_time_histograms(generation_times, render_times, output_dir):
    """Create histogram plots for generation and rendering times."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Generation times histogram
    if generation_times:
        ax1.hist(generation_times, bins=20)
        ax1.set_title('Generation Times Distribution')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Frequency')
        
    # Render times histogram
    if render_times:
        ax2.hist(render_times, bins=20)
        ax2.set_title('Rendering Times Distribution')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig(osp.join(output_dir, 'time_histograms.png'))
    plt.close()

def plot_error_types(error_counter, output_dir):
    """Create a bar chart of error types."""
    if not error_counter:
        return
        
    labels = list(error_counter.keys())
    values = list(error_counter.values())
    
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title('Error Types Distribution')
    plt.xlabel('Error Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(osp.join(output_dir, 'error_types.png'))
    plt.close()

def plot_success_rates(success_rates, output_dir):
    """Create a bar chart of success rates by sample."""
    if not success_rates:
        return
        
    labels = list(success_rates.keys())
    values = list(success_rates.values())
    
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)
    plt.title('Success Rates by Sample')
    plt.xlabel('Sample ID')
    plt.ylabel('Success Rate')
    plt.xticks(rotation=45, ha='right')
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(osp.join(output_dir, 'success_rates.png'))
    plt.close()

def generate_timeline(log_data, output_dir):
    """Generate a timeline visualization of the inference process."""
    # Convert timestamps to seconds from start
    if not log_data:
        return
        
    start_time = datetime.datetime.strptime(log_data[0]['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
    
    timeline_data = []
    for entry in log_data:
        event_time = datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
        seconds = (event_time - start_time).total_seconds()
        
        timeline_data.append({
            'time': seconds,
            'event_type': entry['event_type'],
            'step': entry['step'],
            'message': entry['message']
        })
    
    # Create a timeline visualization
    event_types = sorted(set(entry['event_type'] for entry in timeline_data))
    colors = plt.cm.tab20(np.linspace(0, 1, len(event_types)))
    color_map = dict(zip(event_types, colors))
    
    plt.figure(figsize=(15, 8))
    
    for i, event_type in enumerate(event_types):
        events = [entry for entry in timeline_data if entry['event_type'] == event_type]
        y = [i] * len(events)
        x = [entry['time'] for entry in events]
        
        plt.scatter(x, y, c=[color_map[event_type]], label=event_type, s=30, alpha=0.7)
    
    plt.yticks(range(len(event_types)), event_types)
    plt.xlabel('Time (seconds)')
    plt.title('Inference Process Timeline')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(osp.join(output_dir, 'timeline.png'))
    plt.close()

def generate_report(log_path, output_dir):
    """Generate a comprehensive analysis report from log data."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse logs
    log_data = parse_logs(log_path)
    
    # Analyze data
    generation_times = analyze_generation_times(log_data)
    render_times = analyze_render_times(log_data)
    error_counter = analyze_error_types(log_data)
    success_rates = analyze_success_rates(log_data)
    
    # Generate visualizations
    plot_time_histograms(generation_times, render_times, output_dir)
    plot_error_types(error_counter, output_dir)
    plot_success_rates(success_rates, output_dir)
    generate_timeline(log_data, output_dir)
    
    # Generate text report
    report_path = osp.join(output_dir, 'analysis_report.txt')
    with open(report_path, 'w') as f:
        f.write("# Material Generation and Rendering Analysis Report\n\n")
        
        f.write("## Generation Performance\n")
        if generation_times:
            f.write(f"- Total generations: {len(generation_times)}\n")
            f.write(f"- Average generation time: {np.mean(generation_times):.2f} seconds\n")
            f.write(f"- Median generation time: {np.median(generation_times):.2f} seconds\n")
            f.write(f"- Min generation time: {min(generation_times):.2f} seconds\n")
            f.write(f"- Max generation time: {max(generation_times):.2f} seconds\n\n")
        else:
            f.write("- No generation data available\n\n")
        
        f.write("## Rendering Performance\n")
        if render_times:
            f.write(f"- Total renders: {len(render_times)}\n")
            f.write(f"- Average render time: {np.mean(render_times):.2f} seconds\n")
            f.write(f"- Median render time: {np.median(render_times):.2f} seconds\n")
            f.write(f"- Min render time: {min(render_times):.2f} seconds\n")
            f.write(f"- Max render time: {max(render_times):.2f} seconds\n\n")
        else:
            f.write("- No rendering data available\n\n")
        
        f.write("## Error Analysis\n")
        if error_counter:
            f.write(f"- Total errors: {sum(error_counter.values())}\n")
            f.write("- Error types breakdown:\n")
            for error_type, count in error_counter.most_common():
                f.write(f"  - {error_type}: {count}\n")
            f.write("\n")
        else:
            f.write("- No errors detected\n\n")
        
        f.write("## Success Rates\n")
        if success_rates:
            avg_success = np.mean(list(success_rates.values()))
            f.write(f"- Average success rate: {avg_success:.2%}\n")
            f.write("- Success rates by sample:\n")
            for sample_id, rate in sorted(success_rates.items()):
                f.write(f"  - Sample {sample_id}: {rate:.2%}\n")
        else:
            f.write("- No success rate data available\n")
    
    print(f"Report generated at {output_dir}")
    return report_path

def main():
    parser = argparse.ArgumentParser(description='Analyze material generation and rendering logs')
    parser.add_argument('log_path', type=str, help='Path to the log file')
    parser.add_argument('--output-dir', '-o', type=str, default='log_analysis',
                        help='Directory to save analysis results')
    
    args = parser.parse_args()
    generate_report(args.log_path, args.output_dir)

if __name__ == '__main__':
    main() 