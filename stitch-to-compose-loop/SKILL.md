---
name: stitch-to-compose-loop
description: Converts Google Stitch mockup screens and design specifications into production-ready Jetpack Compose code with iterative syntax and visual diff self-healing.
---

# Stitch-to-Compose Conversion Loop Skill

This skill allows the AI Agent to programmatically convert UI designs from Google Stitch into fully functional, compiling, and visually matching Jetpack Compose code.

## Prerequisites

1. **StitchMCP:** Must be available and active to query screens and design systems.
2. **Python Environment:** The host system must have Python installed.
3. **Android Project:** A valid Android project with Gradle setup.

---

## Configuration & CLI Parameters

All scripts auto-detect the Android project root by searching upwards for a Gradle configuration file (`settings.gradle` or `settings.gradle.kts`). If the default settings do not match your project structure, pass the following options:

* **`setup_roborazzi.py`**
  * `--project-root <path>`: Override the auto-detected Android project root.

* **`render_preview.py`**
  * `composable_name` (Positional): Name of the Composable function to preview.
  * `composable_import` (Positional): Import path or class name of the Composable.
  * `output_image_name` (Positional): Name of the output image file (saved in the skill's `temp/` folder).
  * `--project-root <path>`: Override the auto-detected Android project root.
  * `--package <name>`: Target package for test class placement (default: `io.github.drew_developer.snapshelf`).
  * `--theme <name>`: Custom Theme Composable wrapping the preview (default: `SnapShelfTheme`).
  * `--theme-import <import>`: Package import for the custom theme (default: `io.github.drew_developer.snapshelf.ui.theme.SnapShelfTheme`).
  * `--module <name>`: Target Gradle module containing the UI code (default: `app`).

* **`error_parser.py`**
  * `log_file` (Positional, Optional): Path to the build log file (reads from standard input if omitted).
  * `--project-root <path>`: Override the project root used to generate relative clickable file links.

---

## Execution Flow

### Phase 0: Setup Roborazzi
If this is the first execution, set up Roborazzi dependencies in the project:
1. Run the Python setup script, passing the target project root if it is not auto-detected:
   ```bash
   python stitch-to-compose-loop/scripts/setup_roborazzi.py --project-root <path-to-project-root>
   ```
2. Sync the project by executing:
   ```bash
   ./gradlew dependencies
   ```

### Phase 1: Retrieve Stitch Design Specs
Use `StitchMCP` to fetch design resources for the target screen:
1. Find the target screen ID or list available screens using `StitchMCP:list_screens`.
2. Extract the detail of the screen using `StitchMCP:get_screen`.
3. Read the project-level design tokens (colors, margins, typography) using `StitchMCP:get_project` or `StitchMCP:list_design_systems`.

### Phase 2: Jetpack Compose Code Generation
Create the Composable file:
1. Scaffold the screen using the template [compose_template.kt.tmpl](templates/compose_template.kt.tmpl).
2. Save the generated code to your project's UI folder (e.g. `<project-root>/app/src/main/java/io/github/drew_developer/snapshelf/ui/GeneratedScreen.kt`).
3. **Strict Dynamic Color & Theme Mapping Rules**:
   * **No Static Global References**: Never directly bind hardcoded color constants or static variables (e.g. `PrimaryInk`, `SoftInk`, `WarmSand`, `PaleTaupe` etc.) inside Composable functions. All color rendering must resolve dynamically using the active `MaterialTheme.colorScheme` properties.
   * **Dynamic Canvas Containers**: Always resolve backgrounds and surfaces using M3 containers (e.g. `surface`, `surfaceContainerLow`, `surfaceContainer`) to respect dark mode overrides.
   * **Dynamic Border Separations**: Use `MaterialTheme.colorScheme.outlineVariant` for 1px hairline cards and dividers instead of static gray values.
   * **Multi-State Conditionals (Stood/Density Levels)**: Match progress levels and category tiers 1:1 with corresponding theme properties:
     * *Level 0 (Rest)* -> `MaterialTheme.colorScheme.surface`
     * *Level 1 (Foundation)* -> `MaterialTheme.colorScheme.surfaceVariant`
     * *Level 2 (Balanced)* -> `MaterialTheme.colorScheme.primaryContainer`
     * *Level 3 (Peak)* -> `MaterialTheme.colorScheme.primary`
     * *Anchor state completing* -> `MaterialTheme.colorScheme.secondary` & `onSecondary`
     * *Core state completing* -> `MaterialTheme.colorScheme.primary` & `onPrimary`
     * *Bonus state completing* -> `MaterialTheme.colorScheme.tertiary` & `onTertiary`
   * **Interactivity Feedback**: Track focus changes via `onFocusChanged` for text fields and dynamically update container states (e.g., switching background between `surfaceContainerLow` and `surfaceContainer`) to match the mockup guidance.

### Phase 3: Sandboxed Compiler & Self-Healing Loop
Run compilation checks and self-heal syntax errors:
1. Run compilation for the Kotlin module:
   ```bash
   ./gradlew :app:compileDebugKotlin > stitch-to-compose-loop/temp/compile_log.txt 2>&1
   ```
2. Parse compilation logs:
   ```bash
   python stitch-to-compose-loop/scripts/error_parser.py stitch-to-compose-loop/temp/compile_log.txt --project-root <path-to-project-root>
   ```
3. If compiler errors are found:
   * Map errors back to the code lines in the generated screen file.
   * Correct the code based on the parsed compiler error output.
   * Repeat until compilation succeeds or `max_compiler_retries` (default: 5) is reached.

### Phase 4: Headless Preview & Visual VQA Loop
Compare the rendered layout against the Stitch design:
1. Render the Composable headlessly using Roborazzi:
   ```bash
   python stitch-to-compose-loop/scripts/render_preview.py "GeneratedScreen" "GeneratedScreen" "rendered_preview.png" --project-root <path-to-project-root> --theme <ThemeName> --theme-import <ThemeImportPackage> --package <PackageName>
   ```
   * This executes the Roborazzi JUnit test class and outputs the screenshot to `stitch-to-compose-loop/temp/rendered_preview.png`.
   * The temporary test class is deleted automatically after execution to avoid test pollution.
2. Retrieve the screenshot or mockups of the screen from Stitch.
3. Compare the original mockup and the rendered screenshot.
4. If there are visual layout issues (e.g. alignment mismatch, padding discrepancies, text alignment issues):
   * Generate a visual feedback prompt explaining the discrepancies.
   * Edit the generated screen Composable to fix issues.
   * Re-run Phase 3 and Phase 4.
5. Exit loop when the visual diff results in zero critical discrepancies or `max_vqa_retries` (default: 4) is reached.

---

## Directory Structure

All files relating to this skill are stored in [stitch-to-compose-loop/](.).

* [SKILL.md](SKILL.md)
* Scripts:
  * [setup_roborazzi.py](scripts/setup_roborazzi.py)
  * [render_preview.py](scripts/render_preview.py)
  * [error_parser.py](scripts/error_parser.py)
* Templates:
  * [compose_template.kt.tmpl](templates/compose_template.kt.tmpl)
