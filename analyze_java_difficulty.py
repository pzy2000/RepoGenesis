#!/usr/bin/env python3
"""
Analyze Java repository difficulty based on multiple metrics using Regex.
Similar to analyze_difficulty.py but for Java, without using javalang/lizard.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

# Regex patterns for Java
# Note: These are approximations.
RE_COMMENT_SINGLE = re.compile(r'//.*')
RE_COMMENT_MULTI = re.compile(r'/\*.*?\*/', re.DOTALL)
RE_STRING_DOUBLE = re.compile(r'"(?:\\.|[^"\\])*"')
RE_STRING_SINGLE = re.compile(r"'(?:\\.|[^'\\])*'")

# Complexity keywords
# if, else if, for, while, case, catch, &&, ||, ?
# Note: 'else if' should be counted as 1 (handled by counting 'if').
# We need to be careful not to double count 'else if' as 'else' + 'if'.
# However, usually Cyclomatic Complexity counts predicates. 
# 'else' itself doesn't add a path unless it's 'else if'. 
# Standard simplified CC: +1 for every 'if', 'for', 'while', 'case', 'catch', '&&', '||', '?'
RE_COMPLEXITY = re.compile(r'\b(if|for|while|case|catch)\b|&&|\|\||\?')

# Class/Interface/Enum definitions
RE_CLASS = re.compile(r'\b(class|interface|enum)\s+\w+')

# Method definitions (heuristic)
# Modification/Type/Name (args) {
# e.g., public void test() {
# This is hard with regex. We'll look for:
# \w+ \s+ \w+ \s* \( [^)]* \) \s* (?:throws \w+)? \s* \{
# Simplified: word followed by parenthesis and opening brace
RE_METHOD = re.compile(r'\b\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{') 


def remove_comments_and_strings(code: str) -> str:
    """Remove comments and strings to analyze code structure only."""
    # Remove strings first to avoid modifying comments inside strings or vice-versa
    # But actually, comment markers inside strings should be preserved as string content.
    # And string markers inside comments should be ignored.
    # Proper tokenization is hard with regex. We will do a best-effort approach.
    
    # We'll mask strings first
    def replace_string(match):
        return '""' # Replace with empty string
        
    code = RE_STRING_DOUBLE.sub('""', code)
    code = RE_STRING_SINGLE.sub("''", code)
    
    # Remove multi-line comments
    code = RE_COMMENT_MULTI.sub('', code)
    # Remove single-line comments
    code = RE_COMMENT_SINGLE.sub('', code)
    
    return code

def count_loc(lines: List[str]) -> int:
    """Count non-blank, non-comment lines."""
    # We assume 'lines' are from valid code.
    # We can't easily strip comments line-by-line if we have multi-line comments.
    # So we'll rely on the processed code text for structure, but for LOC we usually use the raw file 
    # filtering full-line comments and blanks.
    
    # Simple approach matching the python script: 
    # "Total non-comment, non-blank lines"
    
    # Let's clean the whole text first
    text = '\n'.join(lines)
    text = RE_COMMENT_MULTI.sub('', text)
    
    # Split back
    new_lines = text.split('\n')
    count = 0
    for line in new_lines:
        line = line.strip()
        # Remove single line comments
        line = RE_COMMENT_SINGLE.sub('', line).strip()
        if line:
            count += 1
    return count

def analyze_java_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Java file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # LOC
        lines = content.split('\n')
        loc = count_loc(lines)
        
        # Structure analysis
        clean_code = remove_comments_and_strings(content)
        
        # Complexity
        # Base complexity is usually 1, but existing script adds 1 + sum(...)
        # For AST visitor in python script:
        # self.complexity += 1  # Base complexity
        # self.complexity += sum(...)
        # So we start with 1 (base for the file/class?) implies at least one path?
        # Typically CC is per function. Sum of CC of all functions.
        # Python script sums complexity of all functions inside classes.
        
        # Let's count complexity tokens
        matches = RE_COMPLEXITY.findall(clean_code)
        complexity_contribution = len(matches)
        
        # Functions/Classes
        classes = len(RE_CLASS.findall(clean_code))
        
        # Methods
        # This regex is messy, might match control structures like 'if (x) {'
        # So we should exclude keywords.
        # However, 'if' is usually not followed by '{' immediately without ')'
        # 'if (cond) {' matches the pattern `\w+\s*\([^)]*\)...` because 'if' is `\w+`
        # We need to exclude keywords from the method start.
        
        potential_methods = RE_METHOD.finditer(clean_code)
        functions = 0
        keywords = {'if', 'while', 'for', 'switch', 'catch', 'synchronized'}
        
        for m in potential_methods:
            match_str = m.group(0)
            # Check the word before the parenthesis
            # match_str looks like "name (" or "name( ..."
            name_part = match_str.split('(')[0].strip()
            # Get the last word
            words = name_part.split()
            if words:
                last_word = words[-1]
                if last_word not in keywords:
                    functions += 1
        
        # Python script adds base complexity (=1) per function.
        # Let's do the same.
        complexity = functions + complexity_contribution
        
        return {
            'loc': loc,
            'complexity': complexity,
            'functions': functions,
            'classes': classes
        }
    except Exception as e:
        # print(f"Error processing {file_path}: {e}")
        return {
            'loc': 0, 'complexity': 0, 'functions': 0, 'classes': 0
        }

def analyze_repository(repo_path: Path) -> Dict[str, Any]:
    """Analyze entire repository."""
    metrics = {
        'total_files': 0,
        'java_files': 0,
        'total_loc': 0,
        'total_complexity': 0,
        'total_functions': 0,
        'total_classes': 0,
        'api_endpoints': 0
    }
    
    exclude_dirs = {'target', 'build', '.git', '.idea', 'node_modules'}
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = Path(root) / file
            
            if file.endswith('.java'):
                # Check for test files (naive exclusion for metrics or inclusion?)
                # Python script: "Total non-comment... lines measuring code volume"
                # Python script logic: "if 'test' in file.lower() ... metrics['test_files'] += 1"
                # But it DOES include them in total_loc etc.
                # "Analyze file ... metrics['total_loc'] += ..." happens for ALL .py files.
                # So we include tests.
                
                metrics['total_files'] += 1
                metrics['java_files'] += 1
                
                file_metrics = analyze_java_file(file_path)
                metrics['total_loc'] += file_metrics['loc']
                metrics['total_complexity'] += file_metrics['complexity']
                metrics['total_functions'] += file_metrics['functions']
                metrics['total_classes'] += file_metrics['classes']
                
    # API Endpoints from README
    readme_path = repo_path / 'README.md'
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                endpoints = re.findall(r'(?:POST|GET|PUT|DELETE|PATCH)\s+[/\w\-{}:]+', readme_content, re.IGNORECASE)
                metrics['api_endpoints'] = len(set(endpoints))
        except:
            pass

    return metrics

def classify_difficulty(metrics: Dict[str, Any]) -> str:
    """Same scoring logic as Python script."""
    score = 0.0
    
    # LOC (25%)
    loc = metrics['total_loc']
    if loc > 1500: score += 2.5
    elif loc > 900: score += 1.5
    elif loc > 500: score += 1.0
    else: score += 0.5
    
    # Complexity (30%)
    complexity = metrics['total_complexity']
    if complexity > 500: score += 3.0
    elif complexity > 300: score += 2.0
    elif complexity > 200: score += 1.2
    else: score += 0.6
    
    # Files (15%) - Using 'java_files' instead of 'python_files'
    files = metrics['java_files']
    if files > 15: score += 1.5
    elif files > 8: score += 1.0
    elif files > 5: score += 0.6
    else: score += 0.3
    
    # APIs (15%)
    apis = metrics['api_endpoints']
    if apis > 15: score += 1.5
    elif apis > 10: score += 1.0
    elif apis > 6: score += 0.6
    else: score += 0.3
    
    # Funcs/Classes (15%)
    total_constructs = metrics['total_functions'] + metrics['total_classes']
    if total_constructs > 100: score += 1.5
    elif total_constructs > 80: score += 1.0
    elif total_constructs > 50: score += 0.6
    else: score += 0.3
    
    if score >= 7.0: return 'Hard'
    elif score >= 4.5: return 'Medium'
    else: return 'Easy'

def main():
    base_path = Path('repo_readme_verified_java')
    if not base_path.exists():
        # Fallback or check relative to current dir
        # base_path = Path('code/repo_readme_verified_java_with_t_p')
        raise Exception("Path not found, using fallback path.")
    results = {}
    
    print("Analyzing Java repositories...")
    print(f"Path: {base_path}")
    
    if base_path.exists():
        for repo_dir in sorted(base_path.iterdir()):
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
                
                # Complexity (30%)
                complexity = metrics['total_complexity']
                if complexity > 500: score += 3.0
                elif complexity > 300: score += 2.0
                elif complexity > 200: score += 1.2
                else: score += 0.6
                
                # Files (15%) - Using 'java_files' instead of 'python_files'
                files = metrics['java_files']
                if files > 15: score += 1.5
                elif files > 8: score += 1.0
                elif files > 5: score += 0.6
                else: score += 0.3
                
                # APIs (15%)
                apis = metrics['api_endpoints']
                if apis > 15: score += 1.5
                elif apis > 10: score += 1.0
                elif apis > 6: score += 0.6
                else: score += 0.3
                
                # Funcs/Classes (15%)
                total_constructs = metrics['total_functions'] + metrics['total_classes']
                if total_constructs > 100: score += 1.5
                elif total_constructs > 80: score += 1.0
                elif total_constructs > 50: score += 0.6
                else: score += 0.3
                
                results[repo_dir.name] = {
                    'metrics': metrics,
                    'difficulty': difficulty,
                    'composite_score': round(score, 2)
                }
    
    # Print Results
    print("\n" + "="*80)
    print("JAVA DIFFICULTY CLASSIFICATION RESULTS")
    print("="*80)
    
    by_difficulty = {'Easy': [], 'Medium': [], 'Hard': []}
    for repo, data in results.items():
        by_difficulty[data['difficulty']].append(repo)
        
    for difficulty in ['Easy', 'Medium', 'Hard']:
        print(f"\n{difficulty}: {len(by_difficulty[difficulty])} repositories")
        for repo in sorted(by_difficulty[difficulty]):
            data = results[repo]
            m = data['metrics']
            print(f"  - {repo}: Score={data['composite_score']:.2f}, LOC={m['total_loc']}, "
                  f"Complexity={m['total_complexity']}, Files={m['java_files']}, "
                  f"APIs={m['api_endpoints']}, Funcs={m['total_functions']}, Classes={m['total_classes']}")

    # Save
    output_file = Path('java_difficulty_classification.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {output_file.absolute()}")

if __name__ == '__main__':
    main()
