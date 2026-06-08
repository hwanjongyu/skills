import os
import re
import sys
import argparse

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

def modify_libs_versions(project_root):
    toml_path = os.path.join(project_root, "gradle", "libs.versions.toml")
    if not os.path.exists(toml_path):
        print(f"Error: libs.versions.toml not found at {toml_path}")
        return False

    with open(toml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if roborazzi is already present
    if "roborazzi" in content:
        print("Roborazzi already present in libs.versions.toml")
        return True

    # Insert into [versions]
    versions_pattern = r"(\[versions\]\n)"
    roborazzi_version = 'roborazzi = "1.21.0"\nrobolectric = "4.12.1"\n'
    content = re.sub(versions_pattern, r"\1" + roborazzi_version, content)

    # Insert into [libraries]
    libraries_pattern = r"(\[libraries\]\n)"
    roborazzi_libraries = (
        'roborazzi = { group = "io.github.takahirom.roborazzi", name = "roborazzi", version.ref = "roborazzi" }\n'
        'roborazzi-compose = { group = "io.github.takahirom.roborazzi", name = "roborazzi-compose", version.ref = "roborazzi" }\n'
        'roborazzi-junit = { group = "io.github.takahirom.roborazzi", name = "roborazzi-junit-rule", version.ref = "roborazzi" }\n'
        'robolectric = { group = "org.robolectric", name = "robolectric", version.ref = "robolectric" }\n'
        'androidx-compose-ui-test-junit4 = { group = "androidx.compose.ui", name = "ui-test-junit4" }\n'
        'androidx-compose-ui-test-manifest = { group = "androidx.compose.ui", name = "ui-test-manifest" }\n'
    )
    content = re.sub(libraries_pattern, r"\1" + roborazzi_libraries, content)

    # Insert into [plugins]
    plugins_pattern = r"(\[plugins\]\n)"
    roborazzi_plugin = 'roborazzi = { id = "io.github.takahirom.roborazzi", version.ref = "roborazzi" }\n'
    content = re.sub(plugins_pattern, r"\1" + roborazzi_plugin, content)

    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully updated {toml_path}")
    return True

def modify_build_gradle(project_root):
    gradle_path = os.path.join(project_root, "app", "build.gradle.kts")
    if not os.path.exists(gradle_path):
        print(f"Error: build.gradle.kts not found at {gradle_path}")
        return False

    with open(gradle_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "roborazzi" in content:
        print("Roborazzi already present in app/build.gradle.kts")
        return True

    # Add plugin to plugins block
    plugins_pattern = r"(plugins\s*\{)"
    roborazzi_plugin_line = "\n    alias(libs.plugins.roborazzi)"
    content = re.sub(plugins_pattern, r"\1" + roborazzi_plugin_line, content)

    # Add dependencies to dependencies block
    dependencies_pattern = r"(dependencies\s*\{)"
    roborazzi_deps = (
        "\n    // Roborazzi Screenshot Testing\n"
        "    testImplementation(libs.roborazzi)\n"
        "    testImplementation(libs.roborazzi.compose)\n"
        "    testImplementation(libs.roborazzi.junit)\n"
        "    testImplementation(libs.robolectric)\n"
        "    debugImplementation(libs.androidx.compose.ui.test.manifest)\n"
        "    testImplementation(libs.androidx.compose.ui.test.junit4)\n"
    )
    content = re.sub(dependencies_pattern, r"\1" + roborazzi_deps, content)

    # Enable robolectric tests to access resources
    if "testOptions" in content:
        if "unitTests" in content:
            if "isIncludeAndroidResources" not in content:
                content = re.sub(r"(unitTests\s*\{)", r"\1\n            isIncludeAndroidResources = true\n", content)
        else:
            content = re.sub(r"(testOptions\s*\{)", r"\1\n        unitTests {\n            isIncludeAndroidResources = true\n        }\n", content)
    else:
        if "android {" in content:
            content = re.sub(r"(android\s*\{)", r"\1\n    testOptions {\n        unitTests {\n            isIncludeAndroidResources = true\n        }\n    }\n", content)
        else:
            print("Warning: Could not find 'android {' block to insert testOptions. Please configure it manually.")

    with open(gradle_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully updated {gradle_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Setup Roborazzi screenshot test configuration.")
    parser.add_argument("--project-root", help="Absolute path to the Android project root.")
    args = parser.parse_args()

    project_root = args.project_root
    if not project_root:
        project_root = find_project_root()
        print(f"Auto-detected Android project root: {project_root}")
    else:
        project_root = os.path.abspath(project_root)
        print(f"Using provided Android project root: {project_root}")

    if not os.path.exists(project_root):
        print(f"Error: Project root directory does not exist: {project_root}")
        sys.exit(1)

    s1 = modify_libs_versions(project_root)
    s2 = modify_build_gradle(project_root)
    if s1 and s2:
        print("Roborazzi setup completed successfully!")
        sys.exit(0)
    else:
        print("Roborazzi setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
