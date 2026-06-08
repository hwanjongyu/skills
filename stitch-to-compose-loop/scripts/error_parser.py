import sys
import re
import json
import os

def find_project_root():
    # Check environment variable
    env_root = os.environ.get("ANDROID_PROJECT_ROOT")
    if env_root and os.path.exists(env_root):
        return os.path.abspath(env_root)
    
    # Walk up from current script directory
    curr = os.path.abspath(os.path.dirname(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(curr, "settings.gradle")) or os.path.exists(os.path.join(curr, "settings.gradle.kts")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
        
    # Check current working directory
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "settings.gradle")) or os.path.exists(os.path.join(cwd, "settings.gradle.kts")):
        return cwd
        
    # Default fallback
    return "/home/drew/AndroidStudioProjects/SnapShelf"

def parse_errors(log_content, project_root):
    # Regex to match Kotlin compiler errors:
    # e: /path/to/file.kt: (12, 34): error message
    # e: /path/to/file.kt:12:34: error message
    pattern_bracket = re.compile(r"^e: (.*?):\((\d+),\s*(\d+)\): (.*)$")
    pattern_colon = re.compile(r"^e: (.*?):(\d+):(\d+): (.*)$")
    
    errors = []
    
    project_root = os.path.abspath(project_root)
    root_prefix = project_root if project_root.endswith(os.sep) else project_root + os.sep
    
    for line in log_content.splitlines():
        line = line.strip()
        match = pattern_bracket.match(line)
        if not match:
            match = pattern_colon.match(line)
            
        if match:
            filepath = match.group(1)
            line_num = int(match.group(2))
            col_num = int(match.group(3))
            message = match.group(4)
            
            # Use relative paths for better readability
            rel_path = filepath
            if filepath.startswith(root_prefix):
                rel_path = filepath[len(root_prefix):]
            elif root_prefix in filepath:
                rel_path = filepath.split(root_prefix, 1)[1]
                
            errors.append({
                "file": rel_path,
                "line": line_num,
                "col": col_num,
                "message": message
            })
            
    return errors

def main():
    # Parse arguments manually to support positional log file with optional --project-root
    project_root = None
    log_file = None
    
    args = sys.argv[1:]
    if "--project-root" in args:
        try:
            idx = args.index("--project-root")
            if idx + 1 < len(args):
                project_root = args[idx + 1]
                # Remove them from args list
                args.pop(idx + 1)
                args.pop(idx)
        except ValueError:
            pass
            
    if args:
        log_file = args[0]
        
    if not project_root:
        project_root = find_project_root()
        
    content = ""
    if log_file:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading log file: {e}")
            sys.exit(1)
    else:
        content = sys.stdin.read()
        
    errors = parse_errors(content, project_root)
    
    if errors:
        print(f"### Found {len(errors)} Compilation Errors\n")
        for idx, err in enumerate(errors, 1):
            abs_filepath = os.path.join(project_root, err['file'])
            print(f"{idx}. **File:** [{err['file']}](file://{abs_filepath}#L{err['line']})")
            print(f"   * **Location:** Line {err['line']}, Col {err['col']}")
            print(f"   * **Error:** `{err['message']}`\n")
    else:
        # Check if the log file indicates a compilation error that was not caught by regex
        # (e.g. Gradle configure failures, Java compile errors, etc.)
        if "BUILD FAILED" in content or "e: " in content or "FAILURE: Build failed" in content:
            print("### Found Build Failures (Kotlin compiler regex did not match details)\n")
            # Print last 15 lines of the build log
            lines = content.splitlines()
            tail_lines = lines[-15:] if len(lines) > 15 else lines
            print("```text")
            print("\n".join(tail_lines))
            print("```")
        else:
            print("No compilation errors found.")

if __name__ == "__main__":
    main()
