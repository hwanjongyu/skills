import sys
import os
import subprocess
import shutil
import platform
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

TEST_TEMPLATE = """package {package}

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.github.takahirom.roborazzi.captureRoboImage
{theme_import}
{composable_import}
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(AndroidJUnit4::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [34], manifest = Config.NONE, qualifiers = "{qualifiers}")
class PreviewScreenshotTest {{
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testRenderPreview() {{
        captureRoboImage("{output_image_path}") {{
            {theme_name} {{
                {composable_name}()
            }}
        }}
    }}
}}
"""

def generate_test_class(test_class_path, composable_name, composable_import, output_image_path, package, theme_name, theme_import, qualifiers):
    test_class_dir = os.path.dirname(test_class_path)
    os.makedirs(test_class_dir, exist_ok=True)
    
    # Resolve imports
    theme_import_line = f"import {theme_import}" if theme_import else ""
    
    if "." not in composable_import:
        composable_import_line = f"import {package}.ui.{composable_import}"
    else:
        composable_import_line = f"import {composable_import}"
        
    # Generate content
    content = TEST_TEMPLATE.format(
        package=package,
        theme_import=theme_import_line,
        theme_name=theme_name,
        composable_import=composable_import_line,
        composable_name=composable_name,
        output_image_path=output_image_path,
        qualifiers=qualifiers
    )
    
    # Write test class
    with open(test_class_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated test file: {test_class_path}")

def run_gradle_test(project_root, module_name, package):
    gradle_bin = "gradlew.bat" if platform.system() == "Windows" else "gradlew"
    gradle_executable = os.path.join(project_root, gradle_bin)
    
    if not os.path.exists(gradle_executable):
        # If gradlew wrapper is missing, fallback to system gradle
        gradle_executable = "gradle"

    cmd = [
        gradle_executable,
        f":{module_name}:testDebugUnitTest",
        "--tests",
        f"{package}.PreviewScreenshotTest",
        "-Proborazzi.test.record=true"
    ]
    print(f"Running command: {' '.join(cmd)}")
    
    # Run Gradle command in project root
    result = subprocess.run(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("=== Gradle stdout ===")
    print(result.stdout)
    print("=== Gradle stderr ===")
    print(result.stderr)
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Render Jetpack Compose previews headlessly.")
    parser.add_argument("composable_name", help="Name of the Composable function to preview.")
    parser.add_argument("composable_import", help="Name or import path of the Composable.")
    parser.add_argument("output_image_name", help="Name of output image file (e.g. rendered_preview.png).")
    
    parser.add_argument("--project-root", help="Absolute path to the Android project root.")
    parser.add_argument("--package", default="io.github.drew_developer.snapshelf", help="Package name for test class placement.")
    parser.add_argument("--theme", default="SnapShelfTheme", help="Theme name to wrap the Composable with.")
    parser.add_argument("--theme-import", default="io.github.drew_developer.snapshelf.ui.theme.SnapShelfTheme", help="Import path for the application theme.")
    parser.add_argument("--module", default="app", help="Gradle module name containing the UI.")
    parser.add_argument("--qualifiers", default="w360dp-h800dp-xhdpi", help="Robolectric device qualifiers for screen dimensions and density.")
    
    # Check if arguments were passed. Standard CLI usage fallback to support positional args
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
        
    # Resolve the skill directory temp path dynamically
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(skill_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    output_image_path = os.path.join(temp_dir, args.output_image_name)
    
    # Clean old preview if exists
    if os.path.exists(output_image_path):
        os.remove(output_image_path)
        
    # Resolve test file destination path dynamically
    package_dir = args.package.replace(".", "/")
    test_class_path = os.path.join(project_root, args.module, "src/test/java", package_dir, "PreviewScreenshotTest.kt")
    
    test_generated = False
    try:
        generate_test_class(
            test_class_path=test_class_path,
            composable_name=args.composable_name,
            composable_import=args.composable_import,
            output_image_path=output_image_path,
            package=args.package,
            theme_name=args.theme,
            theme_import=args.theme_import,
            qualifiers=args.qualifiers
        )
        test_generated = True
        
        success = run_gradle_test(project_root, args.module, args.package)
        if success and os.path.exists(output_image_path):
            print(f"Screenshot successfully generated at: {output_image_path}")
            sys.exit(0)
        else:
            print("Failed to generate screenshot. Check Gradle logs above.")
            sys.exit(1)
    finally:
        # Avoid test pollution by cleaning up the generated test class file
        if test_generated and os.path.exists(test_class_path):
            try:
                os.remove(test_class_path)
                print("Cleaned up temporary test file successfully.")
            except Exception as e:
                print(f"Warning: Failed to clean up test class file: {e}")

if __name__ == "__main__":
    main()
