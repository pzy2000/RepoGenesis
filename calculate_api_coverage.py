#!/usr/bin/env python3
"""
API Coverage (AC) Calculator

This script calculates API Coverage for each repository based on the definition:
AC = (1/|R|) * Σ (|{api ∈ A_r : implemented(api, C_r)}| / |A_r|)

Where:
- R is the set of all repositories
- A_r is the set of required API endpoints for repository r (from README)
- C_r is the codebase of repository r
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

def extract_api_endpoints_from_readme(readme_path: str) -> List[Dict[str, str]]:
    """
    Extract API endpoints and features from README.md
    
    Returns:
        List of dictionaries containing endpoint information:
        [{
            'method': 'GET/POST/PUT/DELETE',
            'path': '/api/...',
            'description': '...'
        }]
    """
    if not os.path.exists(readme_path):
        return []
    
    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    endpoints = []
    
    # Pattern 1: Explicit API endpoint format: METHOD /path - Description
    # e.g., "POST /api/users - Create a new user"
    pattern1 = re.compile(r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s\-]+)\s*[-:]?\s*(.+?)(?:\n|$)', re.IGNORECASE)
    for match in pattern1.finditer(content):
        endpoints.append({
            'method': match.group(1).upper(),
            'path': match.group(2).strip(),
            'description': match.group(3).strip()
        })
    
    # Pattern 2: API table format
    # Look for table rows with method and path
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
    # Look for endpoints in code blocks marked with ```
    code_blocks = re.findall(r'```[\w]*\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for match in pattern1.finditer(block):
            endpoints.append({
                'method': match.group(1).upper(),
                'path': match.group(2).strip(),
                'description': match.group(3).strip()
            })
    
    # Pattern 4: Feature list format (e.g., "- Health Check")
    # Extract features that might be API endpoints
    feature_pattern = re.compile(r'[-*]\s+([A-Z][A-Za-z\s]+(?:Check|Login|Register|Create|Update|Delete|Get|List|Manage|Service|API))', re.MULTILINE)
    features = feature_pattern.findall(content)
    for feature in features:
        # Convert feature name to potential endpoint
        feature_clean = feature.strip()
        if len(endpoints) == 0:  # Only add if no explicit endpoints found
            endpoints.append({
                'method': 'FEATURE',
                'path': feature_clean,
                'description': feature_clean
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
    """
    Search for implementation of an API endpoint in the codebase
    
    Args:
        repo_path: Path to repository
        endpoint: Endpoint dictionary with method, path, description
    
    Returns:
        True if endpoint appears to be implemented, False otherwise
    """
    method = endpoint['method']
    path = endpoint['path']
    description = endpoint['description']
    
    # Search patterns for different frameworks
    search_patterns = []
    
    # Clean path for searching (remove parameters, etc.)
    clean_path = re.sub(r'[{}<>:]', '', path)
    path_parts = [p for p in clean_path.split('/') if p and not p.startswith(':')]
    
    if method == 'FEATURE':
        # For feature-based endpoints, search for the feature name
        search_patterns.append(path.lower().replace(' ', '_'))
        search_patterns.append(path.lower().replace(' ', ''))
    else:
        # Flask/FastAPI decorators: @app.get("/path") or @app.route("/path", methods=["GET"])
        search_patterns.append(f'@app.{method.lower()}')
        search_patterns.append(f'@router.{method.lower()}')
        search_patterns.append(f'@bp.{method.lower()}')
        search_patterns.append(f'methods=["{method}"')
        search_patterns.append(f"methods=['{method}'")
        
        # Django: urlpatterns with path
        for part in path_parts:
            search_patterns.append(f"'{part}'")
            search_patterns.append(f'"{part}"')
        
        # Express/Node.js: app.get("/path")
        search_patterns.append(f'app.{method.lower()}')
        search_patterns.append(f'router.{method.lower()}')
        
        # Spring Boot: @GetMapping, @PostMapping, etc.
        search_patterns.append(f'@{method.title()}Mapping')
        
        # Path parts for general matching
        search_patterns.extend(path_parts)
    
    # Search in Python, Java, JavaScript files
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
                        
                        # Check if any pattern exists in file
                        for pattern in search_patterns:
                            if pattern and pattern in content:
                                # Additional verification: check if path is nearby
                                if method != 'FEATURE':
                                    # Look for the actual path in the same file
                                    if path in content or any(part in content for part in path_parts if len(part) > 3):
                                        return True
                                else:
                                    return True
                except Exception as e:
                    continue
    
    return False


def calculate_api_coverage(repo_base_path: str) -> Dict:
    """
    Calculate API coverage for all repositories in the base path
    
    Returns:
        Dictionary with repository names as keys and coverage data as values
    """
    results = {}
    repos = sorted([d for d in os.listdir(repo_base_path) 
                   if os.path.isdir(os.path.join(repo_base_path, d)) and not d.startswith('.')])
    
    for repo_name in repos:
        repo_path = os.path.join(repo_base_path, repo_name)
        readme_path = os.path.join(repo_path, 'README.md')
        
        print(f"\n{'='*80}")
        print(f"Processing: {repo_name}")
        print(f"{'='*80}")
        
        # Extract API endpoints from README
        endpoints = extract_api_endpoints_from_readme(readme_path)
        print(f"Found {len(endpoints)} API endpoints/features in README")
        
        if len(endpoints) == 0:
            results[repo_name] = {
                'total_apis': 0,
                'implemented_apis': 0,
                'coverage': 0.0,
                'endpoints': [],
                'note': 'No API endpoints found in README'
            }
            continue
        
        # Check implementation for each endpoint
        implemented = []
        not_implemented = []
        
        for i, endpoint in enumerate(endpoints, 1):
            print(f"  [{i}/{len(endpoints)}] Checking: {endpoint['method']} {endpoint['path']}")
            is_implemented = search_implementation(repo_path, endpoint)
            
            if is_implemented:
                implemented.append(endpoint)
                print(f"    ✓ FOUND")
            else:
                not_implemented.append(endpoint)
                print(f"    ✗ NOT FOUND")
        
        coverage = len(implemented) / len(endpoints) if len(endpoints) > 0 else 0.0
        
        results[repo_name] = {
            'total_apis': len(endpoints),
            'implemented_apis': len(implemented),
            'coverage': coverage,
            'endpoints': {
                'implemented': implemented,
                'not_implemented': not_implemented
            }
        }
        
        print(f"\nCoverage: {len(implemented)}/{len(endpoints)} = {coverage:.2%}")
    
    return results


def generate_latex_table(results: Dict) -> str:
    """Generate LaTeX table from results"""
    
    lines = []
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{API Coverage (AC) for Repositories in repo\\_readme\\_1219\\_deepcode\\_gpt-5.2}")
    lines.append("\\label{tab:api_coverage}")
    lines.append("\\begin{tabular}{lrrr}")
    lines.append("\\toprule")
    lines.append("Repository & Total APIs & Implemented & Coverage (\\%) \\\\")
    lines.append("\\midrule")
    
    total_apis = 0
    total_implemented = 0
    
    for repo_name, data in sorted(results.items()):
        repo_display = repo_name.replace('_', '\\_')
        total = data['total_apis']
        implemented = data['implemented_apis']
        coverage = data['coverage'] * 100
        
        total_apis += total
        total_implemented += implemented
        
        lines.append(f"{repo_display} & {total} & {implemented} & {coverage:.1f} \\\\")
    
    lines.append("\\midrule")
    overall_coverage = (total_implemented / total_apis * 100) if total_apis > 0 else 0
    lines.append(f"\\textbf{{Overall}} & {total_apis} & {total_implemented} & {overall_coverage:.1f} \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    
    return '\n'.join(lines)


def main():
    repo_base_path = "code/exps/repos/repo_readme_1219_deepcode_gpt-5.2"
    
    print("Starting API Coverage Calculation...")
    print(f"Repository base path: {repo_base_path}")
    
    # Calculate coverage
    results = calculate_api_coverage(repo_base_path)
    
    # Save results to JSON
    output_json = "code/api_coverage_results.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n\nResults saved to: {output_json}")
    
    # Generate LaTeX table
    latex_table = generate_latex_table(results)
    output_tex = "code/api_coverage_table.tex"
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(latex_table)
    print(f"LaTeX table saved to: {output_tex}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_apis = sum(r['total_apis'] for r in results.values())
    total_implemented = sum(r['implemented_apis'] for r in results.values())
    overall_ac = (total_implemented / total_apis) if total_apis > 0 else 0
    
    print(f"\nTotal repositories analyzed: {len(results)}")
    print(f"Total API endpoints found: {total_apis}")
    print(f"Total implemented: {total_implemented}")
    print(f"Overall API Coverage (AC): {overall_ac:.2%}")
    
    print("\n" + latex_table)


if __name__ == "__main__":
    main()
