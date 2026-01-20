#!/usr/bin/env python3
"""
Comprehensive API Coverage Calculator for repos_IDE directory

This script calculates API Coverage for all repositories across different 
IDE-model configurations and generates a comprehensive LaTeX table.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """Extract API endpoints and features from README.md"""
    if not os.path.exists(readme_path):
        return []
    
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    endpoints = []
    
    # Pattern 1: Explicit API endpoint format: METHOD /path - Description
    pattern1 = re.compile(r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s\-]+)\s*[-:]?\s*(.+?)(?:\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({
            'method': match.group(1).upper(),
            'path': match.group(2).strip(),
            'description': match.group(3).strip()
        })
    
    # Pattern 2: API table format
    table_pattern = re.compile(r'\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*([^\|]+?)\s*\|', re.IGNORECASE)
    for match in table_pattern.finditer(content):
        path = match.group(2).strip()
        if path.startswith('/') or path.startswith('`/'):
            path = path.strip('`').strip()
            endpoints.append({
                'method': match.group(1).upper(),
                'path': path,
                'description': ''
            })
    
    # Pattern 3: Code block endpoints
    code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({
                'method': match.group(1).upper(),
                'path': match.group(2).strip(),
                'description': match.group(3).strip()
            })
    
    # Remove duplicates
    seen = set()
    unique_endpoints = []
    for ep in endpoints:
        key = f"{ep['method']}:{ep['path']}"
        if key not in seen:
            seen.add(key)
            unique_endpoints.append(ep)
    
    return unique_endpoints


def search_implementation(repo_path: str, endpoint: Dict[str, str]) -> bool:
    """Search for implementation of an API endpoint in the codebase"""
    method = endpoint['method']
    path = endpoint['path']
    
    # Clean path for searching
    clean_path = re.sub(r'[{}<>:]', '', path)
    path_parts = [p for p in clean_path.split('/') if p and not p.startswith(':')]
    
    # Search patterns for different frameworks
    search_patterns = []
    
    # Flask/FastAPI decorators
    search_patterns.append(f'@app.{method.lower()}')
    search_patterns.append(f'@router.{method.lower()}')
    search_patterns.append(f'@bp.{method.lower()}')
    search_patterns.append(f'methods=["{method}"')
    search_patterns.append(f"methods=['{method}'")
    
    # Django patterns
    for part in path_parts:
        search_patterns.append(f"'{part}'")
        search_patterns.append(f'"{part}"')
    
    # Spring Boot
    search_patterns.append(f'@{method.title()}Mapping')
    
    # Path parts
    search_patterns.extend(path_parts)
    
    # Search in source files
    extensions = ['.py', '.java', '.js', '.ts', '.kt']
    
    for root, dirs, files in os.walk(repo_path):
        # Skip test directories, build outputs, and dependency caches
        # CRITICAL: Tests should NOT be counted as implementation
        dirs[:] = [d for d in dirs if d not in [
            '.git', '__pycache__', 'node_modules', 'venv', '.venv', 
            'target', 'build', 'test', 'tests', '.pytest_cache'
        ]]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        for pattern in search_patterns:
                            if pattern and pattern in content:
                                # Verify path is nearby
                                if path in content or any(part in content for part in path_parts if len(part) > 3):
                                    return True
                except Exception:
                    continue
    
    return False


def parse_repo_dirname(dirname: str) -> Dict[str, str]:
    """
    Parse repository directory name to extract metadata
    
    Expected format: repo_readme_MMDD_IDE_model_Language
    Example: repo_readme_1216_antigravity_gemini3pro_Java
    """
    parts = dirname.split('_')
    
    # Find indices
    date_idx = None
    for i, part in enumerate(parts):
        if part.isdigit() and len(part) == 4:
            date_idx = i
            break
    
    if date_idx is None:
        return None
    
    # Extract components
    date = parts[date_idx]
    
    # Find language (Java or Python) - usually at the end
    language = None
    language_idx = None
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].lower() in ['java', 'python']:
            language = parts[i].capitalize()
            language_idx = i
            break
    
    if language is None:
        return None
    
    # IDE and model are between date and language
    ide_model_parts = parts[date_idx + 1:language_idx]
    
    if not ide_model_parts:
        return None
    
    # First part is IDE
    ide_raw = ide_model_parts[0].lower()
    # Map to match DSR table names
    if ide_raw == 'vscode':
        ide = 'Copilot'
    elif ide_raw == 'antigravity':
        ide = 'Antigravity'
    else:
        ide = ide_model_parts[0].capitalize()

    
    # Rest is model
    model = '_'.join(ide_model_parts[1:]) if len(ide_model_parts) > 1 else 'unknown'
    
    return {
        'date': date,
        'ide': ide,
        'model': model,
        'language': language,
        'full_name': dirname
    }


def calculate_ac_for_all_repos(base_path: str) -> Dict:
    """Calculate API Coverage for all repositories in repos_IDE"""
    
    # Get all repo directories
    repo_dirs = [d for d in os.listdir(base_path) 
                if os.path.isdir(os.path.join(base_path, d)) and not d.startswith('.')]
    
    results_by_config = defaultdict(lambda: {
        'repos': [],
        'total_apis': 0,
        'implemented_apis': 0,
        'coverage': 0.0
    })
    
    all_results = {}
    
    for repo_dir in sorted(repo_dirs):
        config_path = os.path.join(base_path, repo_dir)
        config_info = parse_repo_dirname(repo_dir)
        
        if not config_info:
            print(f"Skipping invalid directory name: {repo_dir}")
            continue
        
        print(f"\n{'='*80}")
        print(f"Processing Configuration: {repo_dir}")
        print(f"  IDE: {config_info['ide']}")
        print(f"  Model: {config_info['model']}")
        print(f"  Language: {config_info['language']}")
        print(f"{'='*80}")
        
        # Get all repos in this configuration
        repos = [r for r in os.listdir(config_path) 
                if os.path.isdir(os.path.join(config_path, r)) and not r.startswith('.')]
        
        config_key = (config_info['ide'], config_info['model'], config_info['language'])
        
        for repo_name in sorted(repos):
            repo_path = os.path.join(config_path, repo_name)
            readme_path = os.path.join(repo_path, 'README.md')
            
            print(f"  Analyzing: {repo_name}")
            
            # Extract API endpoints
            endpoints = extract_api_endpoints_from_readme(readme_path)
            
            if len(endpoints) == 0:
                print(f"    No API endpoints found")
                continue
            
            # Check implementation
            implemented = 0
            for endpoint in endpoints:
                if search_implementation(repo_path, endpoint):
                    implemented += 1
            
            coverage = implemented / len(endpoints) if len(endpoints) > 0 else 0.0
            
            print(f"    APIs: {implemented}/{len(endpoints)} = {coverage:.2%}")
            
            # Store results
            repo_result = {
                'repo_name': repo_name,
                'total_apis': len(endpoints),
                'implemented_apis': implemented,
                'coverage': coverage
            }
            
            results_by_config[config_key]['repos'].append(repo_result)
            results_by_config[config_key]['total_apis'] += len(endpoints)
            results_by_config[config_key]['implemented_apis'] += implemented
        
        # Calculate config coverage
        if results_by_config[config_key]['total_apis'] > 0:
            results_by_config[config_key]['coverage'] = (
                results_by_config[config_key]['implemented_apis'] / 
                results_by_config[config_key]['total_apis']
            )
    
    return dict(results_by_config)


def generate_latex_table(results: Dict) -> str:
    """Generate LaTeX table similar to DSR table format"""
    
    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{API Coverage (AC) across IDE-model configurations. Results demonstrate API implementation completeness across 9 IDE-model-language combinations.}")
    lines.append("\\label{tab:ac_comprehensive}")
    lines.append("\\resizebox{\\columnwidth}{!}{%")
    lines.append("\\begin{tabular}{llccc}")
    lines.append("\\toprule")
    lines.append("\\textbf{IDE} & \\textbf{Model} & \\textbf{Language} & \\textbf{Implemented/Total} & \\textbf{AC} \\\\")
    lines.append("\\midrule")
    
    # Group by IDE
    by_ide = defaultdict(list)
    for (ide, model, language), data in sorted(results.items()):
        by_ide[ide].append((model, language, data))
    
    # Calculate overall
    total_apis = sum(data['total_apis'] for data in results.values())
    total_implemented = sum(data['implemented_apis'] for data in results.values())
    overall_ac = (total_implemented / total_apis * 100) if total_apis > 0 else 0
    
    first_ide = True
    for ide, configs in sorted(by_ide.items()):
        if not first_ide:
            lines.append("\\midrule")
        first_ide = False
        
        # Sort by model, then language
        configs = sorted(configs, key=lambda x: (x[0], x[1]))
        
        # Count rows for multirow
        num_rows = len(configs)
        
        for idx, (model, language, data) in enumerate(configs):
            total = data['total_apis']
            implemented = data['implemented_apis']
            ac = data['coverage'] * 100
            
            # Format model name to match DSR table style
            model_display = model.replace('_', ' ').replace('-', ' ')
            
            # Special handling for common model names
            if 'gpt' in model.lower() and '5' in model:
                if 'mini' in model.lower():
                    model_display = 'GPT-5 Mini'
                elif '5.1' in model or '51' in model:
                    model_display = 'GPT-5.1 Codex'
                else:
                    model_display = model_display.upper()
            elif 'claude' in model.lower():
                if '4' in model and '5' in model:
                    model_display = 'Claude 4.5 Sonnet'
                else:
                    model_display = 'Claude ' + model.replace('claude', '').strip('_- ')
            elif 'gemini' in model.lower():
                if 'low' in model.lower():
                    model_display = 'Gemini 3 Pro (Low)'
                elif '3' in model and 'pro' in model.lower():
                    model_display = 'Gemini 3 Pro'
                else:
                    model_display = 'Gemini ' + model.replace('gemini', '').strip('_- ').replace('3pro', '3 Pro')
            elif 'grok' in model.lower():
                model_display = 'Grok'
            else:
                # Default: capitalize each word
                model_display = ' '.join(word.capitalize() for word in model_display.split())

            
            if idx == 0:
                # First row with IDE name
                lines.append(f"\\multirow{{{num_rows}}}{{*}}{{{ide}}} & {model_display} & {language} & {implemented}/{total} & {ac:.2f}\\% \\\\")
            else:
                # Subsequent rows
                lines.append(f"& {model_display} & {language} & {implemented}/{total} & {ac:.2f}\\% \\\\")
    
    lines.append("\\midrule")
    lines.append(f"\\multicolumn{{3}}{{l}}{{\\textbf{{Overall}}}} & \\textbf{{{total_implemented}/{total_apis}}} & \\textbf{{{overall_ac:.2f}\\%}} \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("}")
    lines.append("\\end{table}")
    
    return '\n'.join(lines)


def main():
    base_path = "code/exps/repos_IDE"
    
    print("Starting API Coverage Calculation for repos_IDE...")
    print(f"Base path: {base_path}")
    
    # Calculate coverage
    results = calculate_ac_for_all_repos(base_path)
    
    # Save results to JSON
    output_json = "code/api_coverage_ide_results.json"
    
    # Convert tuple keys to strings for JSON serialization
    results_serializable = {
        f"{ide}|{model}|{language}": data 
        for (ide, model, language), data in results.items()
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)
    print(f"\n\nResults saved to: {output_json}")
    
    # Generate LaTeX table
    latex_table = generate_latex_table(results)
    output_tex = "code/api_coverage_ide_table.tex"
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    print(f"LaTeX table saved to: {output_tex}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_configs = len(results)
    total_apis = sum(data['total_apis'] for data in results.values())
    total_implemented = sum(data['implemented_apis'] for data in results.values())
    overall_ac = (total_implemented / total_apis) if total_apis > 0 else 0
    
    print(f"\nTotal configurations analyzed: {total_configs}")
    print(f"Total API endpoints found: {total_apis}")
    print(f"Total implemented: {total_implemented}")
    print(f"Overall API Coverage (AC): {overall_ac:.2%}")
    
    print("\n" + "="*80)
    print("BY CONFIGURATION")
    print("="*80)
    
    for (ide, model, language), data in sorted(results.items()):
        print(f"\n{ide} - {model} - {language}:")
        print(f"  Total APIs: {data['total_apis']}")
        print(f"  Implemented: {data['implemented_apis']}")
        print(f"  Coverage: {data['coverage']:.2%}")
        print(f"  Repositories: {len(data['repos'])}")
    
    print("\n" + latex_table)


if __name__ == "__main__":
    main()
