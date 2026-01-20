#!/usr/bin/env python3
"""
Visualize repository difficulty classification metrics.
Generates figures for paper presentation.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from datetime import datetime

# Set publication-quality style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'


def load_classification_data():
    """Load classification results from JSON."""
    json_path = Path('../code/java_difficulty_classification.json')
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_difficulty_distribution(data, output_dir):
    """Plot distribution of repositories by difficulty."""
    difficulties = {}
    for repo, info in data.items():
        diff = info['difficulty']
        if diff != 'Unclassified' and info.get('metrics'):
            difficulties[diff] = difficulties.get(diff, 0) + 1
    
    # Create bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    
    categories = ['Easy', 'Medium', 'Hard']
    counts = [difficulties.get(cat, 0) for cat in categories]
    colors = ['#2ecc71', '#f39c12', '#e74c3c']
    
    bars = ax.bar(categories, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Number of Repositories', fontsize=12, fontweight='bold')
    ax.set_xlabel('Difficulty Level', fontsize=12, fontweight='bold')
    ax.set_title('Distribution of Repositories by Difficulty', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(counts) + 1)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    time = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(output_dir / f'difficulty_distribution_{time}.pdf', bbox_inches='tight')
    plt.savefig(output_dir / f'difficulty_distribution_{time}.png', bbox_inches='tight')
    print(f"Saved: {output_dir / f'difficulty_distribution_{time}.pdf'}")
    plt.close()


def plot_metrics_comparison(data, output_dir):
    """Plot comparison of metrics across difficulty levels."""
    metrics_by_difficulty = {'Easy': [], 'Medium': [], 'Hard': []}
    
    for repo, info in data.items():
        diff = info['difficulty']
        if diff != 'Unclassified' and info.get('metrics'):
            m = info['metrics']
            metrics_by_difficulty[diff].append({
                'repo': repo,
                'loc': m['total_loc'],
                'complexity': m['total_complexity'],
                'files': m['python_files'] if 'python_files' in m else m['java_files'],
                'apis': m['api_endpoints'],
                'score': info.get('composite_score', 0)
            })
    
    # Create subplots for different metrics
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle('Repository Complexity Metrics by Difficulty Level', fontsize=14, fontweight='bold')
    
    metrics_info = [
        ('loc', 'Lines of Code (LOC)', 0, 0),
        ('complexity', 'Cyclomatic Complexity', 0, 1),
        ('files', 'Number of Files', 0, 2),
        ('apis', 'API Endpoints', 1, 0),
        ('score', 'Composite Score', 1, 1)
    ]
    
    colors = {'Easy': '#2ecc71', 'Medium': '#f39c12', 'Hard': '#e74c3c'}
    
    for metric_key, metric_label, row, col in metrics_info:
        ax = axes[row, col]
        
        positions = []
        values = []
        labels = []
        bar_colors = []
        
        x_pos = 0
        for diff in ['Easy', 'Medium', 'Hard']:
            for item in metrics_by_difficulty[diff]:
                positions.append(x_pos)
                values.append(item[metric_key])
                labels.append(item['repo'])
                bar_colors.append(colors[diff])
                x_pos += 1
            x_pos += 0.5  # Gap between difficulty groups
        
        bars = ax.bar(positions, values, color=bar_colors, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax.set_ylabel(metric_label, fontsize=10, fontweight='bold')
        ax.set_xlabel('Repositories', fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Remove x-axis labels for cleaner look
        ax.set_xticks([])
    
    # Remove the empty subplot
    fig.delaxes(axes[1, 2])
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='#2ecc71', edgecolor='black', label='Easy'),
        mpatches.Patch(facecolor='#f39c12', edgecolor='black', label='Medium'),
        mpatches.Patch(facecolor='#e74c3c', edgecolor='black', label='Hard')
    ]
    fig.legend(handles=legend_elements, loc='lower right', bbox_to_anchor=(0.95, 0.15), fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'metrics_comparison.pdf', bbox_inches='tight')
    plt.savefig(output_dir / 'metrics_comparison.png', bbox_inches='tight')
    print(f"Saved: {output_dir / 'metrics_comparison.pdf'}")
    plt.close()


def plot_score_distribution(data, output_dir):
    """Plot composite score distribution with difficulty thresholds."""
    scores = []
    difficulties = []
    repo_names = []
    
    for repo, info in data.items():
        if info['difficulty'] != 'Unclassified' and info.get('metrics'):
            scores.append(info.get('composite_score', 0))
            difficulties.append(info['difficulty'])
            repo_names.append(repo)
    
    # Sort by score
    sorted_indices = np.argsort(scores)
    scores = [scores[i] for i in sorted_indices]
    difficulties = [difficulties[i] for i in sorted_indices]
    repo_names = [repo_names[i] for i in sorted_indices]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    
    colors = {'Easy': '#2ecc71', 'Medium': '#f39c12', 'Hard': '#e74c3c'}
    bar_colors = [colors[d] for d in difficulties]
    
    positions = range(len(scores))
    bars = ax.bar(positions, scores, color=bar_colors, alpha=0.7, edgecolor='black', linewidth=1.2)
    
    # Add difficulty threshold lines
    ax.axhline(y=4.5, color='blue', linestyle='--', linewidth=2, label='Easy/Medium Threshold (4.5)')
    ax.axhline(y=7.0, color='red', linestyle='--', linewidth=2, label='Medium/Hard Threshold (7.0)')
    
    ax.set_ylabel('Composite Score', fontsize=12, fontweight='bold')
    ax.set_xlabel('Repositories', fontsize=12, fontweight='bold')
    ax.set_title('Repository Composite Scores with Difficulty Thresholds', fontsize=13, fontweight='bold')
    ax.set_xticks(positions)
    ax.set_xticklabels(repo_names, rotation=45, ha='right', fontsize=9)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    ax.set_ylim(0, 11)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='#2ecc71', edgecolor='black', label='Easy'),
        mpatches.Patch(facecolor='#f39c12', edgecolor='black', label='Medium'),
        mpatches.Patch(facecolor='#e74c3c', edgecolor='black', label='Hard'),
        plt.Line2D([0], [0], color='blue', linestyle='--', linewidth=2, label='Easy/Medium (4.5)'),
        plt.Line2D([0], [0], color='red', linestyle='--', linewidth=2, label='Medium/Hard (7.0)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    plt.tight_layout()
    time = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(output_dir / f'score_distribution_{time}.pdf', bbox_inches='tight')
    plt.savefig(output_dir / f'score_distribution_{time}.png', bbox_inches='tight')
    print(f"Saved: {output_dir / f'score_distribution_{time}.pdf'}")
    plt.close()


def plot_metric_correlation(data, output_dir):
    """Plot correlation between LOC and Cyclomatic Complexity."""
    locs = []
    complexities = []
    difficulties = []
    repo_names = []
    
    for repo, info in data.items():
        if info['difficulty'] != 'Unclassified' and info.get('metrics'):
            m = info['metrics']
            locs.append(m['total_loc'])
            complexities.append(m['total_complexity'])
            difficulties.append(info['difficulty'])
            repo_names.append(repo)
    
    # Create scatter plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    colors = {'Easy': '#2ecc71', 'Medium': '#f39c12', 'Hard': '#e74c3c'}
    
    for diff in ['Easy', 'Medium', 'Hard']:
        diff_locs = [locs[i] for i, d in enumerate(difficulties) if d == diff]
        diff_complexities = [complexities[i] for i, d in enumerate(difficulties) if d == diff]
        diff_names = [repo_names[i] for i, d in enumerate(difficulties) if d == diff]
        
        ax.scatter(diff_locs, diff_complexities, c=colors[diff], label=diff, 
                   s=200, alpha=0.7, edgecolors='black', linewidth=1.5)
        
        # Add repository labels
        for x, y, name in zip(diff_locs, diff_complexities, diff_names):
            ax.annotate(name, (x, y), xytext=(5, 5), textcoords='offset points', 
                       fontsize=8, alpha=0.8)
    
    ax.set_xlabel('Lines of Code (LOC)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cyclomatic Complexity', fontsize=12, fontweight='bold')
    ax.set_title('Correlation between LOC and Cyclomatic Complexity', fontsize=13, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    time = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(output_dir / f'metric_correlation_{time}.pdf', bbox_inches='tight')
    plt.savefig(output_dir / f'metric_correlation_{time}.png', bbox_inches='tight')
    print(f"Saved: {output_dir / f'metric_correlation_{time}.pdf'}")
    plt.close()


def generate_summary_table(data, output_dir):
    """Generate LaTeX table for paper."""
    latex_content = []
    latex_content.append("% Auto-generated difficulty classification table")
    latex_content.append("\\begin{table}[htbp!]")
    latex_content.append("\\centering")
    latex_content.append("\\caption{Detailed complexity metrics for repository difficulty classification.}")
    latex_content.append("\\label{tab:difficulty-metrics-full}")
    latex_content.append("\\resizebox{\\linewidth}{!}{")
    latex_content.append("\\begin{tabular}{lcccccccc}")
    latex_content.append("\\toprule")
    latex_content.append("\\textbf{Repository} & \\textbf{LOC} & \\textbf{Complexity} & \\textbf{Files} & \\textbf{APIs} & \\textbf{Functions} & \\textbf{Classes} & \\textbf{Score} & \\textbf{Difficulty} \\\\")
    latex_content.append("\\midrule")
    
    # Group by difficulty
    by_difficulty = {'Easy': [], 'Medium': [], 'Hard': []}
    for repo, info in data.items():
        if info['difficulty'] != 'Unclassified' and info.get('metrics'):
            by_difficulty[info['difficulty']].append((repo, info))
    
    # Sort each group by score
    for diff in ['Easy', 'Medium', 'Hard']:
        items = sorted(by_difficulty[diff], key=lambda x: x[1].get('composite_score', 0))
        
        if items and diff != 'Easy':
            latex_content.append("\\midrule")
        
        for repo, info in items:
            m = info['metrics']
            score = info.get('composite_score', 0)
            latex_content.append(
                f"{repo.replace('_', ' ')} & {m['total_loc']} & {m['total_complexity']} & "
                f"{m['python_files'] if 'python_files' in m else m['java_files']} & {m['api_endpoints']} & {m['total_functions']} & "
                f"{m['total_classes']} & {score:.2f} & {diff} \\\\"
            )
    
    latex_content.append("\\bottomrule")
    latex_content.append("\\end{tabular}")
    latex_content.append("}")
    latex_content.append("\\end{table}")
    
    # Save LaTeX table
    latex_file = output_dir / 'difficulty_table.tex'
    with open(latex_file, 'w') as f:
        f.write('\n'.join(latex_content))
    
    print(f"Saved: {latex_file}")


def main():
    """Generate all visualizations."""
    print("="*80)
    print("REPOSITORY DIFFICULTY VISUALIZATION")
    print("="*80)
    
    # Load data
    data = load_classification_data()
    
    # Create output directory
    output_dir = Path('../paper/680cd8c5-a759-4e47-8287-883a008d6398/figs')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"\nGenerating visualizations in: {output_dir}\n")
    
    # Generate plots
    plot_difficulty_distribution(data, output_dir)
    plot_metrics_comparison(data, output_dir)
    plot_score_distribution(data, output_dir)
    plot_metric_correlation(data, output_dir)
    generate_summary_table(data, output_dir)
    
    print("\n" + "="*80)
    print("All visualizations generated successfully!")
    print("="*80)


if __name__ == '__main__':
    main()

