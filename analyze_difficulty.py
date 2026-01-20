#!/usr/bin/env python3
"""
Analyze repository difficulty based on multiple metrics.
Similar to GAIA benchmark's difficulty classification.
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any
import re


class ComplexityAnalyzer(ast.NodeVisitor):
    """Calculate cyclomatic complexity of Python code."""
    
    def __init__(self):
        self.complexity = 0
        self.functions = 0
        self.classes = 0
        
    def visit_FunctionDef(self, node):
        self.functions += 1
        self.complexity += 1  # Base complexity
        self.complexity += sum(1 for _ in ast.walk(node) if isinstance(_, (
            ast.If, ast.While, ast.For, ast.ExceptHandler,
            ast.With, ast.Assert, ast.BoolOp, ast.Compare
        )))
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
        
    def visit_ClassDef(self, node):
        self.classes += 1
        self.generic_visit(node)


def count_code_tokens(code: str) -> int:
    """Estimate token count (simple whitespace-based approximation)."""
    return len(code.split())


def analyze_python_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Count lines
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Parse AST
        try:
            tree = ast.parse(content)
            analyzer = ComplexityAnalyzer()
            analyzer.visit(tree)
            
            return {
                'loc': loc,
                'complexity': analyzer.complexity,
                'functions': analyzer.functions,
                'classes': analyzer.classes,
                'tokens': count_code_tokens(content)
            }
        except SyntaxError:
            return {
                'loc': loc,
                'complexity': 0,
                'functions': 0,
                'classes': 0,
                'tokens': count_code_tokens(content)
            }
    except Exception as e:
        return {
            'loc': 0,
            'complexity': 0,
            'functions': 0,
            'classes': 0,
            'tokens': 0
        }


def analyze_repository(repo_path: Path) -> Dict[str, Any]:
    """Analyze entire repository."""
    metrics = {
        'total_files': 0,
        'python_files': 0,
        'total_loc': 0,
        'total_complexity': 0,
        'total_functions': 0,
        'total_classes': 0,
        'total_tokens': 0,
        'test_files': 0,
        'api_endpoints': 0
    }
    
    # Exclude certain directories
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache', 'data', 'logs', 'uploads'}
    
    for root, dirs, files in os.walk(repo_path):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = Path(root) / file
            
            # Count all files
            if file.endswith('.py'):
                metrics['total_files'] += 1
                metrics['python_files'] += 1
                
                # Check if test file
                if 'test' in file.lower() or 'test' in str(file_path).lower():
                    metrics['test_files'] += 1
                
                # Analyze file
                file_metrics = analyze_python_file(file_path)
                metrics['total_loc'] += file_metrics['loc']
                metrics['total_complexity'] += file_metrics['complexity']
                metrics['total_functions'] += file_metrics['functions']
                metrics['total_classes'] += file_metrics['classes']
                metrics['total_tokens'] += file_metrics['tokens']
    
    # Try to count API endpoints from README
    readme_path = repo_path / 'README.md'
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                # Look for common API endpoint patterns
                endpoints = re.findall(r'(?:POST|GET|PUT|DELETE|PATCH)\s+[/\w\-{}:]+', readme_content, re.IGNORECASE)
                metrics['api_endpoints'] = len(set(endpoints))
        except:
            pass
    
    return metrics


def classify_difficulty(metrics: Dict[str, Any]) -> str:
    """
    Classify repository difficulty based on multiple metrics.
    
    Criteria (inspired by GAIA benchmark):
    - Easy: Simple services with basic CRUD operations, minimal complexity
    - Medium: Services with moderate complexity, authentication, and business logic
    - Hard: Complex services with advanced features, real-time processing, or intricate logic
    
    Metrics considered:
    - Lines of Code (LOC): Code volume
    - Cyclomatic Complexity: Logic complexity
    - File Count: Project structure complexity
    - API Endpoints: Interface complexity
    - Functions/Classes: Code organization complexity
    - Code Tokens: Overall code density
    """
    
    # Composite score calculation (weighted)
    score = 0.0
    
    # LOC contribution (weight: 25%)
    loc = metrics['total_loc']
    if loc > 1500:
        score += 2.5
    elif loc > 900:
        score += 1.5
    elif loc > 500:
        score += 1.0
    else:
        score += 0.5
    
    # Complexity contribution (weight: 30%)
    complexity = metrics['total_complexity']
    if complexity > 500:
        score += 3.0
    elif complexity > 300:
        score += 2.0
    elif complexity > 200:
        score += 1.2
    else:
        score += 0.6
    
    # Number of files contribution (weight: 15%)
    files = metrics['python_files']
    if files > 20:
        score += 1.5
    elif files > 12:
        score += 1.0
    elif files > 5:
        score += 0.6
    else:
        score += 0.3
    
    # API endpoints contribution (weight: 15%)
    apis = metrics['api_endpoints']
    if apis > 12:
        score += 1.5
    elif apis > 8:
        score += 1.0
    elif apis > 5:
        score += 0.6
    else:
        score += 0.3
    
    # Functions/Classes contribution (weight: 15%)
    total_constructs = metrics['total_functions'] + metrics['total_classes']
    if total_constructs > 100:
        score += 1.5
    elif total_constructs > 60:
        score += 1.0
    elif total_constructs > 40:
        score += 0.6
    else:
        score += 0.3
    
    # Classification based on composite score
    # Max score: ~10, Min score: ~2
    if score >= 7.0:
        return 'Hard'
    elif score >= 4.5:
        return 'Medium'
    else:
        return 'Easy'


def main():
    """Main analysis function."""
    base_path = Path('../code')
    
    # Directories to analyze
    # scratch_golden_oracle_path = base_path / 'repo_scratch_golden_oracle'
    scratch_golden_oracle_path = base_path / 'caonima'
    golden_oracle_path = base_path / 'repo_readme_1203_msagent_golden_oracle'

    readme_path = base_path / 'repo_readme'
    
    results = {}
    
    # Analyze repo_scratch_golden_oracle
    print("Analyzing repo_scratch_golden_oracle repositories...")
    if scratch_golden_oracle_path.exists():
        for repo_dir in sorted(scratch_golden_oracle_path.iterdir()):
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                print(f"  Analyzing {repo_dir.name}...")
                metrics = analyze_repository(repo_dir)
                difficulty = classify_difficulty(metrics)
                
                # Calculate composite score for display
                score = 0.0
                loc = metrics['total_loc']
                if loc > 1500: score += 2.5
                elif loc > 900: score += 1.5
                elif loc > 500: score += 1.0
                else: score += 0.5
                
                complexity = metrics['total_complexity']
                if complexity > 500: score += 3.0
                elif complexity > 300: score += 2.0
                elif complexity > 200: score += 1.2
                else: score += 0.6
                
                files = metrics['python_files']
                if files > 20: score += 1.5
                elif files > 12: score += 1.0
                elif files > 5: score += 0.6
                else: score += 0.3
                
                apis = metrics['api_endpoints']
                if apis > 12: score += 1.5
                elif apis > 8: score += 1.0
                elif apis > 5: score += 0.6
                else: score += 0.3
                
                total_constructs = metrics['total_functions'] + metrics['total_classes']
                if total_constructs > 100: score += 1.5
                elif total_constructs > 60: score += 1.0
                elif total_constructs > 40: score += 0.6
                else: score += 0.3
                
                results[repo_dir.name] = {
                    'path': 'repo_scratch_golden_oracle',
                    'metrics': metrics,
                    'difficulty': difficulty,
                    'composite_score': round(score, 2)
                }
    
    # Analyze repo_golden_oracle (real-world GitHub repositories)
    print("\nAnalyzing repo_golden_oracle repositories...")
    if golden_oracle_path.exists():
        for repo_dir in sorted(golden_oracle_path.iterdir()):
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                print(f"  Analyzing {repo_dir.name}...")
                metrics = analyze_repository(repo_dir)
                difficulty = classify_difficulty(metrics)
                
                # Calculate composite score for display
                score = 0.0
                loc = metrics['total_loc']
                if loc > 1500: score += 2.5
                elif loc > 900: score += 1.5
                elif loc > 500: score += 1.0
                else: score += 0.5
                
                complexity = metrics['total_complexity']
                if complexity > 500: score += 3.0
                elif complexity > 300: score += 2.0
                elif complexity > 200: score += 1.2
                else: score += 0.6
                
                files = metrics['python_files']
                if files > 20: score += 1.5
                elif files > 12: score += 1.0
                elif files > 5: score += 0.6
                else: score += 0.3
                
                apis = metrics['api_endpoints']
                if apis > 12: score += 1.5
                elif apis > 8: score += 1.0
                elif apis > 5: score += 0.6
                else: score += 0.3
                
                total_constructs = metrics['total_functions'] + metrics['total_classes']
                if total_constructs > 100: score += 1.5
                elif total_constructs > 60: score += 1.0
                elif total_constructs > 40: score += 0.6
                else: score += 0.3
                
                results[repo_dir.name] = {
                    'path': 'repo_golden_oracle',
                    'metrics': metrics,
                    'difficulty': difficulty,
                    'composite_score': round(score, 2)
                }
    
    # For repo_readme, we need to check if there's a corresponding golden oracle
    # If not in golden_oracle, check repo_readme
    print("\nAnalyzing repo_readme repositories...")
    if readme_path.exists():
        for repo_dir in sorted(readme_path.iterdir()):
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                # Only analyze if not already analyzed from golden_oracle
                if repo_dir.name not in results:
                    print(f"  {repo_dir.name} - marking as unclassified (no golden oracle)")
                    results[repo_dir.name] = {
                        'path': 'repo_readme',
                        'metrics': {},
                        'difficulty': 'Unclassified'
                    }
    
    # Print results
    print("\n" + "="*80)
    print("DIFFICULTY CLASSIFICATION RESULTS")
    print("="*80)
    
    # Group by difficulty
    by_difficulty = {'Easy': [], 'Medium': [], 'Hard': [], 'Unclassified': []}
    for repo_name, data in results.items():
        by_difficulty[data['difficulty']].append(repo_name)
    
    for difficulty in ['Easy', 'Medium', 'Hard', 'Unclassified']:
        print(f"\n{difficulty}: {len(by_difficulty[difficulty])} repositories")
        for repo in sorted(by_difficulty[difficulty]):
            data = results[repo]
            if data['metrics']:
                m = data['metrics']
                score = data.get('composite_score', 0)
                print(f"  - {repo}: Score={score:.2f}, LOC={m['total_loc']}, "
                      f"Complexity={m['total_complexity']}, Files={m['python_files']}, "
                      f"APIs={m['api_endpoints']}, Funcs={m['total_functions']}, Classes={m['total_classes']}")
            else:
                print(f"  - {repo}: (no golden oracle implementation)")
    
    # Save to JSON
    output_file = base_path / 'repository_difficulty_classification.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total repositories analyzed: {len(results)}")
    print(f"  Easy: {len(by_difficulty['Easy'])}")
    print(f"  Medium: {len(by_difficulty['Medium'])}")
    print(f"  Hard: {len(by_difficulty['Hard'])}")
    print(f"  Unclassified: {len(by_difficulty['Unclassified'])}")
    
    # Count by source
    scratch_count = sum(1 for r in results.values() if r.get('path') == 'repo_scratch_golden_oracle' and r['metrics'])
    golden_count = sum(1 for r in results.values() if r.get('path') == 'repo_golden_oracle' and r['metrics'])
    print(f"\nClassified by source:")
    print(f"  From repo_scratch_golden_oracle: {scratch_count}")
    print(f"  From repo_golden_oracle: {golden_count}")
    print(f"  Total classified: {scratch_count + golden_count}")


if __name__ == '__main__':
    main()

