"""
Repository README Generator using Groq API
Analyzes any codebase and generates comprehensive README documentation
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Set
import mimetypes
from groq import Groq

class RepositoryAnalyzer:
    def __init__(self, api_key: str):
        """Initialize with Groq API key"""
        self.client = Groq(api_key=api_key)
        # Supported file extensions for text/code/config files (extensive list)
        self.supported_extensions = {
            # Programming languages
            '.py', '.pyw', '.ipynb', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
            '.java', '.kt', '.kts', '.scala', '.groovy', '.rb', '.php', '.pl', '.pm', '.pm6',
            '.c', '.h', '.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hh', '.hxx', '.h++',
            '.cs', '.fs', '.fsx', '.fsi', '.vb', '.vbs', '.swift', '.go', '.rs', '.dart',
            '.m', '.mm', '.r', '.jl', '.lua', '.sh', '.bash', '.zsh', '.fish', '.bat', '.cmd', '.ps1',
            '.asm', '.s', '.S', '.v', '.sv', '.vhd', '.vhdl', '.ada', '.d', '.nim', '.ml', '.mli',
            '.clj', '.cljs', '.cljc', '.edn', '.groovy', '.kt', '.kts', '.erl', '.hrl', '.ex', '.exs',
            '.coffee', '.litcoffee', '.scm', '.ss', '.lisp', '.el', '.rkt', '.raku', '.cr', '.pony',
            '.f', '.f90', '.f95', '.f03', '.f08', '.for', '.ftn', '.f77', '.m4', '.awk', '.ps1', '.psm1',
            # Web/markup
            '.html', '.htm', '.xhtml', '.shtml', '.xml', '.xsd', '.xsl', '.xslt', '.svg', '.rss', '.atom',
            '.css', '.scss', '.sass', '.less', '.styl', '.vue', '.ejs', '.hbs', '.mustache', '.jinja', '.twig',
            # Data/config
            '.json', '.jsonc', '.json5', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env', '.rc',
            '.properties', '.prop', '.prefs', '.plist', '.config', '.tsconfig', '.babelrc', '.editorconfig',
            '.dockerignore', '.npmignore', '.gitattributes', '.gitmodules', '.gitconfig', '.npmrc', '.yarnrc',
            '.lock', '.requirements', '.gradle', '.maven', '.pom', '.sbt', '.gemspec', '.gemfile', '.cargo',
            '.cargo.toml', '.cargo.lock', '.go', '.go.mod', '.go.sum', '.mod', '.sum', '.composer.json', '.composer.lock',
            '.bower.json', '.bowerrc', '.tslint', '.eslint', '.prettierrc', '.stylelintrc', '.pylintrc', '.flake8',
            '.coveragerc', '.travis.yml', '.circleci', '.appveyor.yml', '.azure-pipelines.yml', '.github', '.gitlab-ci.yml',
            '.editorconfig', '.dependabot.yml', '.renovate.json', '.vscode', '.idea', '.vs', '.settings', '.launch',
            # Documentation
            '.md', '.markdown', '.mdown', '.mkd', '.rst', '.adoc', '.asciidoc', '.txt', '.textile', '.rdoc', '.pod',
            '.org', '.creole', '.mediawiki', '.wiki', '.tex', '.latex', '.bib', '.rmd', '.ipynb',
            # Scripts/build
            '.makefile', '.mk', '.mak', '.cmake', '.gradle', '.bat', '.cmd', '.ps1', '.sh', '.bash', '.zsh', '.fish',
            '.dockerfile', '.docker-compose.yml', '.compose', '.build', '.ninja', '.bazel', '.bzl', '.buck', '.justfile',
            # Misc
            '.log', '.out', '.err', '.lst', '.list', '.csv', '.tsv', '.psv', '.dat', '.data', '.db', '.sql', '.sqlite',
            '.dbml', '.dump', '.schema', '.parquet', '.orc', '.avro', '.feather', '.h5', '.hdf5',
            # Templates
            '.tpl', '.tmpl', '.template', '.jinja', '.j2', '.mustache', '.hbs', '.ejs', '.liquid', '.njk', '.nunjucks',
            # Others
            '.license', '.licence', '.copying', '.changelog', '.changes', '.news', '.todo', '.credits', '.authors',
            '.readme', '.readme.md', '.readme.txt', '.manifest', '.about', '.version', '.releasenotes', '.release',
        }
        
    def is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file that should be analyzed"""
        if file_path.suffix.lower() in self.supported_extensions:
            return True
        
        # Check if it's a text file by mime type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text/'):
            return True
            
        # Check common files without extensions
        if file_path.name.lower() in ['makefile', 'dockerfile', 'readme', 'license', 'changelog']:
            return True
            
        return False
    
    def should_skip_directory(self, dir_name: str) -> bool:
        """Check if directory should be skipped"""
        skip_dirs = {
            'node_modules', '.git', '.svn', '.hg', '__pycache__',
            '.pytest_cache', '.mypy_cache', 'venv', 'env', '.env',
            'build', 'dist', '.next', '.nuxt', 'target', 'bin', 'obj',
            '.idea', '.vscode', '.vs', 'coverage', '.coverage',
            'logs', 'log', 'tmp', 'temp', '.tmp', '.temp'
        }
        return dir_name.lower() in skip_dirs or dir_name.startswith('.')
    
    def analyze_repository(self, repo_path: str) -> Dict:
        """Analyze repository structure and content"""
        repo_path = Path(repo_path).resolve()
        
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        analysis = {
            'repo_name': repo_path.name,
            'repo_path': str(repo_path),
            'structure': {},
            'files': {},
            'languages': set(),
            'frameworks': set(),
            'dependencies': {},
            'config_files': [],
            'total_files': 0,
            'total_lines': 0,
            'file_contents_for_ai': []  # Store content for AI analysis
        }
        
        # Walk through directory tree
        for root, dirs, files in os.walk(repo_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not self.should_skip_directory(d)]
            
            root_path = Path(root)
            relative_root = root_path.relative_to(repo_path)
            
            for file in files:
                file_path = root_path / file
                relative_file_path = file_path.relative_to(repo_path)
                
                if self.is_text_file(file_path):
                    try:
                        analysis['total_files'] += 1
                        
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        lines = len(content.splitlines())
                        analysis['total_lines'] += lines
                        
                        # Store file info
                        analysis['files'][str(relative_file_path)] = {
                            'size': len(content),
                            'lines': lines,
                            'extension': file_path.suffix,
                            'content': content[:2000] if len(content) > 2000 else content  # Limit content for API
                        }
                        
                        # Detect language
                        if file_path.suffix:
                            analysis['languages'].add(file_path.suffix.lower())
                        
                        # Store content for AI analysis (key files only)
                        if self.is_key_file_for_analysis(file_path, content):
                            analysis['file_contents_for_ai'].append({
                                'path': str(relative_file_path),
                                'content': content[:1500],  # Limit for AI context
                                'extension': file_path.suffix
                            })
                        
                        # Basic file type detection (non-AI)
                        self.detect_basic_file_types(file_path, content, analysis)
                        
                    except Exception as e:
                        print(f"Warning: Could not read file {file_path}: {e}")
        
        # Use AI to detect frameworks and technologies
        print("Using AI to detect frameworks and technologies...")
        ai_detected = self.ai_detect_frameworks_and_technologies(analysis)
        analysis['frameworks'].update(ai_detected.get('frameworks', []))
        analysis['technologies'] = ai_detected.get('technologies', [])
        analysis['project_type'] = ai_detected.get('project_type', 'Unknown')
        
        # Convert sets to lists for JSON serialization
        analysis['languages'] = list(analysis['languages'])
        analysis['frameworks'] = list(analysis['frameworks'])
        
        # Remove temporary AI content to save memory
        del analysis['file_contents_for_ai']
        
        return analysis
    
    def is_key_file_for_analysis(self, file_path: Path, content: str) -> bool:
        """Determine if file is important for AI framework detection"""
        filename = file_path.name.lower()
        
        # Configuration and package files
        if filename in ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 
                       'cargo.toml', 'go.mod', 'composer.json', 'pyproject.toml', 
                       'setup.py', 'dockerfile', 'docker-compose.yml', 'makefile']:
            return True
        
        # Main application files
        if any(name in filename for name in ['main', 'index', 'app', 'server', '__init__']):
            return True
        
        # Files with imports/includes that reveal frameworks
        if len(content) > 100 and any(keyword in content.lower()[:500] for keyword in 
                                    ['import', 'require', 'include', 'using', 'from']):
            return True
        
        return False
    
    def ai_detect_frameworks_and_technologies(self, analysis: Dict) -> Dict:
        """Use AI to detect frameworks, technologies, and project type"""
        
        # Prepare context for AI
        context = f"""
Analyze this codebase to detect frameworks, technologies, and project type.

Repository: {analysis['repo_name']}
File extensions found: {', '.join(analysis['languages'])}
Total files: {analysis['total_files']}

Key file contents:
"""
        
        # Add file contents for analysis
        for file_info in analysis['file_contents_for_ai'][:10]:  # Limit to avoid token limits
            context += f"\n--- {file_info['path']} ---\n{file_info['content']}\n"
        
        prompt = f"""
Based on the codebase analysis below, identify:

1. **Frameworks**: All frameworks being used (e.g., React, Django, Express.js, Spring Boot, etc.)
2. **Technologies**: Technologies, libraries, and tools (e.g., Docker, Redis, PostgreSQL, etc.)
3. **Project Type**: What type of project this is (e.g., Web Application, API, CLI Tool, Library, etc.)

Be comprehensive and look for evidence in:
- Package/dependency files (package.json, requirements.txt, etc.)
- Import statements and includes
- Configuration files
- Code patterns and structure

Return your analysis as a JSON object with this exact structure:
{{
    "frameworks": ["Framework1", "Framework2", ...],
    "technologies": ["Technology1", "Technology2", ...],
    "project_type": "Project Type Description"
}}

Codebase Analysis:
{context}

Respond with ONLY the JSON object, no additional text:
"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer who can identify frameworks, technologies, and project types from code. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",
                max_tokens=1000,
                temperature=0.3
            )
            
            response_content = chat_completion.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(response_content)
            except json.JSONDecodeError:
                # Extract JSON from response if it contains extra text
                import re
                json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    print("Warning: Could not parse AI response for framework detection")
                    return {"frameworks": [], "technologies": [], "project_type": "Unknown"}
            
        except Exception as e:
            print(f"Warning: AI framework detection failed: {e}")
            return {"frameworks": [], "technologies": [], "project_type": "Unknown"}
    
    def detect_basic_file_types(self, file_path: Path, content: str, analysis: Dict):
        """Basic file type detection for config files and dependencies"""
        filename = file_path.name.lower()
        
        # Just detect config files and basic package managers
        config_files = [
            'package.json', 'yarn.lock', 'package-lock.json',
            'requirements.txt', 'pyproject.toml', 'setup.py', 'pipfile',
            'pom.xml', 'build.gradle', 'build.gradle.kts',
            'cargo.toml', 'cargo.lock',
            'go.mod', 'go.sum',
            'composer.json', 'composer.lock',
            'dockerfile', 'docker-compose.yml',
            'makefile', '.gitignore', 'readme.md'
        ]
        
        if filename in config_files:
            analysis['config_files'].append(str(file_path))
            
        # Extract basic dependencies from package.json only
        if filename == 'package.json':
            try:
                package_data = json.loads(content)
                if 'dependencies' in package_data:
                    analysis['dependencies'].update(package_data['dependencies'])
                if 'devDependencies' in package_data:
                    analysis['dependencies'].update(package_data['devDependencies'])
            except:
                pass

    def generate_readme(self, analysis: Dict) -> str:
        """Generate README using Groq API"""
        
        # Prepare context for the AI
        context = f"""
Repository Analysis:
- Name: {analysis['repo_name']}
- Total Files: {analysis['total_files']}
- Total Lines of Code: {analysis['total_lines']}
- Languages: {', '.join(analysis['languages'])}
- Frameworks/Technologies: {', '.join(analysis['frameworks'])}
- Configuration files: {', '.join(analysis['config_files'])}

File Structure (sample):
"""
        
        # Add sample of file structure
        file_list = list(analysis['files'].keys())[:20]  # Limit for API context
        for file_path in file_list:
            file_info = analysis['files'][file_path]
            context += f"- {file_path} ({file_info['lines']} lines)\n"
        
        if len(analysis['files']) > 20:
            context += f"... and {len(analysis['files']) - 20} more files\n"
        
        # Add sample code snippets from key files
        context += "\nKey File Contents (snippets):\n"
        important_files = [f for f in file_list if any(name in f.lower() for name in 
                          ['main', 'index', 'app', 'server', '__init__', 'setup'])][:5]
        
        for file_path in important_files:
            if file_path in analysis['files']:
                content = analysis['files'][file_path]['content']
                context += f"\n--- {file_path} ---\n{content[:500]}...\n"
        
        prompt = f"""
Based on the following repository analysis, generate a comprehensive README.md file that includes:
NOTE IF U DONT FIND INFO ON ANY OF THE FOLLOWING SKIP THAT SECTION ALWAYS FOLLOW THIS RULE.
1. **Project Title and Description**: Clear, engaging description of what the project does
2. **Features**: Key features and capabilities
3. **Technology Stack**: Languages, frameworks, and tools used
4. **Prerequisites**: System requirements and dependencies 
5. **Installation**: Step-by-step setup instructions IF ANY REQUIRED
6. **Usage**: How to run and use the project with examples
7. **Project Structure**: Overview of the codebase organization
8. **Configuration**: Any environment variables or config files needed
9. **API Documentation**: If applicable, document key endpoints or functions IF ANY PRESENT
10. **Contributing**: Guidelines for contributors
11. **License**: License information IF ALREADY MENTIONED
12. **Contact**: Author/maintainer information IF ALREADY MENTIONED

Make the README professional, well-formatted with proper markdown, and comprehensive enough that someone can understand and set up the project from scratch.

Repository Analysis:
{context}

Generate a complete README.md file:
"""

        try:
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical writer and software developer. Generate comprehensive, professional README files that are clear, well-structured, and include all necessary information for users to understand and use the project."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.1-8b-instant",  # Fast and good for documentation
                max_tokens=4000,
                temperature=0.7
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error generating README with Groq API: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive README for any repository")
    parser.add_argument("repo_path", help="Path to the repository (local path or will be cloned)")
    parser.add_argument("--api-key", help="Groq API key (or set GROQ_API_KEY env var)")
    parser.add_argument("--output", "-o", default="README.md", help="Output file name")
    parser.add_argument("--clone", help="Git URL to clone repository")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('GROQ_API_KEY')
    if not api_key:
        print("Error: Groq API key required. Use --api-key or set GROQ_API_KEY environment variable")
        sys.exit(1)
    
    try:
        # Clone repository if URL provided
        if args.clone:
            print(f"Cloning repository from {args.clone}...")
            os.system(f"git clone {args.clone} {args.repo_path}")
        
        # Initialize analyzer
        analyzer = RepositoryAnalyzer(api_key)
        
        # Analyze repository
        print(f"Analyzing repository: {args.repo_path}")
        analysis = analyzer.analyze_repository(args.repo_path)
        
        print(f"Found {analysis['total_files']} files with {analysis['total_lines']} total lines")
        print(f"Languages detected: {', '.join(analysis['languages'])}")
        print(f"Frameworks detected: {', '.join(analysis['frameworks'])}")
        
        # Generate README
        print("Generating README with Groq AI...")
        readme_content = analyzer.generate_readme(analysis)
        
        # Save README
        output_path = Path(args.repo_path) / args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"README generated successfully: {output_path}")
        
        # Also save analysis for reference
        analysis_path = Path(args.repo_path) / "repository_analysis.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            # Remove content from files to reduce size
            analysis_copy = analysis.copy()
            for file_path in analysis_copy['files']:
                analysis_copy['files'][file_path] = {
                    k: v for k, v in analysis_copy['files'][file_path].items() 
                    if k != 'content'
                }
            json.dump(analysis_copy, f, indent=2)
        
        print(f"Repository analysis saved: {analysis_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
