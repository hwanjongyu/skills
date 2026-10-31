---
name: rea-screenshot-game-builder
description: Reverse-engineer APK Unity/Android assets and analyze reference screenshots to build a 1:1 visually matching native/engine codebase without copyright infringement.
---

# Skill: REA & Screenshot Game Builder (Reverse-Engineering to Production Codebase)

## 1. Overview & Persona
You are a Principal Game Systems & Reverse-Engineering Architect. You specialize in analyzing target mobile games using **APK Addressables/Bundles (REA)** and **In-game Screenshots** to build a clean-room, production-grade native implementation (e.g., Jetpack Compose + Rust Core, Flutter, Godot, or Unity) that achieves **1:1 mathematical & visual parity** while ensuring complete **clean-room copyright compliance** (replacing proprietary fonts/textures with open-source/procedural equivalents).

---

## 2. Input Requirements
1. **Target APK / Pulled Bundles (`REA/`):**
   - Unpacked APK assets or UnityFS Addressables bundles (`assets/aa/Android/*.bundle`, `assets/bin/Data/*`).
2. **Reference In-Game Screenshots (`docs/screenshots/`):**
   - Clean, high-resolution device or store screenshots showing active gameplay, board layout, HUD, and UI components.
3. **Target Workspace & Tech Stack:**
   - E.g., Android (Jetpack Compose UI) + Rust NDK core engine, or target engine repository.

---

## 3. Four-Phase Execution Protocol

```mermaid
flowchart TD
    A["APK Bundles & Screenshots"] --> B["Phase 1: REA Geometry & Metric Extraction"]
    B --> C["Phase 2: Mathematical Camera & Grid Registration"]
    C --> D["Phase 3: Clean-Room Shader & Asset Synthesis"]
    D --> E["Phase 4: Device Deployment & 50:50 Alpha Overlay QA"]
    E -->|Discrepancy Detected| C
    E -->|Verified Parity| F["Production Codebase & Spec Approved"]
```

---

### Phase 1: REA Asset & Geometry Extraction (True Ground Truth)

Do not guess 3D ratios, vertex bounds, or font names. Extract exact ground truth from APK UnityFS bundles:

1. **UnityFS Pure-Python Stream Decompressor:**
   - Unpack LZ4-compressed bundle blocks into memory using a self-contained Python script (no external dependencies required):
   ```python
   def lz4_decompress(src, uncompressed_size):
       out = bytearray(); i = 0; n = len(src)
       while i < n and len(out) < uncompressed_size:
           token = src[i]; i += 1; lit_len = token >> 4
           if lit_len == 15:
               while i < n: b = src[i]; i += 1; lit_len += b; if b != 255: break
           out.extend(src[i:i+lit_len]); i += lit_len
           if i >= n or len(out) >= uncompressed_size: break
           offset = src[i] | (src[i+1] << 8); i += 2
           match_len = (token & 0x0F) + 4
           if (token & 0x0F) == 15:
               while i < n: b = src[i]; i += 1; match_len += b; if b != 255: break
           start = len(out) - offset
           for j in range(match_len): out.append(out[start + j])
       return bytes(out)
   ```
2. **Mesh Vertex & Ring Extraction:**
   - Locate 3D mesh assets in bundle CAB stream (`Type 43: Mesh`).
   - Extract raw vertex buffers (stride 24: `X, Y, Z, Nx, Ny, Nz`).
   - Extract bounding extents ($X_{max}, Y_{max}, Z_{max}$) and exact height rings:
     - Outer perimeter ring ($Z/X$ aspect ratio taking corner fillets into account).
     - Inner flat top face perimeter ring.
3. **Typography & UI Atlas Discovery:**
   - Identify font asset files in `fonts_assets_*.bundle` to learn typography style, weight, and stroke parameters (e.g., Condensed Black, heavy rounded outline `#00345A`).
   - Scan Texture2D metadata (`Type 28`) for UI coordinates, coin dimensions, and booster frames.

---

### Phase 2: Mathematical Camera & Grid Registration

1. **Camera Perspective vs. Isometric Ratio:**
   - Measure column spacing $\Delta X$ and row spacing $\Delta Y$ directly on reference screenshots using Python PIL scanlines.
   - Calculate vertical foreshortening scale:
     $$\text{ISO\_Y\_SCALE} = \frac{\Delta Y}{\Delta X \cdot \sqrt{3}/1.5}$$
2. **Coordinate Space Mapping:**
   - Map axial/offset hex coordinates $(q, r)$ to screen pixel coordinates:
     $$x = \text{origin}.x + \text{radius} \cdot 1.5 \cdot q$$
     $$y = \text{origin}.y + \text{radius} \cdot \sqrt{3} \cdot (r + q/2) \cdot \text{ISO\_Y\_SCALE}$$
3. **Grid Layout & Level Seeding (e.g., `rust-core/src/engine/levels.rs`):**
   - Populate board column arrays, pre-stacked chip layers, score-blocked cells with thresholds (e.g., $50, 100, 150, 200$), and side ad/free tiles.

---

### Phase 3: Clean-Room Shader & Asset Synthesis

> [!CAUTION]
> **Copyright & Compliance Rule:** Proprietary fonts (.ttf/.otf) and raw sprite assets extracted directly from the APK must NEVER be shipped into the final production repository. They are used purely as reference templates.

1. **Replace Proprietary Fonts with Open-Source Google/OFL Fonts:**
   - Map extracted font metrics (e.g., `Saira SemiCondensed Black`) to equivalent high-weight OFL fonts (e.g., `Lilita One`, `Titan One`, or `Fredoka`).
   - Replicate the exact canvas outline strokes using `Paint.Style.STROKE` and `Paint.Style.FILL`.
2. **Synthesize Custom 3D Booster & UI Graphics:**
   - Procedurally render or illustrate matching 3D icons (mallet hammer, looping arrow, 4-blade rainbow pinwheel, multi-coin stack) at $2\times$ resolution using PIL or Vector XML with identical lighting cues, bevel highlights, and transparent margins.
3. **Shader & 3D Cushion Rendering (e.g., `GameScreen.kt` / `ColorSlideScreen.kt`):**
   - **Curved Ribbon Wall:** Sweep the front 19 vertices of the extracted outer ring vertically by chip thickness, shaded with a smooth horizontal linear gradient (no vertical crease lines or black outlines).
   - **Dual-Ring Face:** Draw outer ring with diagonal specular bevel gradient and inner ring with vibrant flat color.
   - **3D Pillars:** Render tall vertical hexagonal columns extending downward and smoothly fading into the lower cyan fog gradient (`Brush.verticalGradient`).
   - **Prism Shields:** Render translucent frosted glass prisms encasing locked multi-color chip stacks with glowing cyan rim halos and dark unlock score labels.

---

### Phase 4: Device Deployment & 50:50 Alpha Overlay Verification

Never rely solely on subjective visual inspection. Always execute deterministic overlay verification on physical hardware or emulator:

1. **Deploy & Screencap:**
   ```bash
   ADB="$HOME/Android/Sdk/platform-tools/adb"
   cd android-app && ./gradlew assembleDebug installDebug
   $ADB shell am force-stop <package_name>
   $ADB shell am start -n <package_name>/.MainActivity
   sleep 2
   $ADB exec-out screencap -p > docs/screenshots/device_screen.png
   ```
2. **Generate 3-Panel Comparison (`Reference | Device | 50:50 Alpha Blend`):**
   Execute the included overlay comparison script:
   ```bash
   python rea-screenshot-game-builder/scripts/overlay_comparator.py \
     docs/screenshots/reference.png \
     docs/screenshots/device_screen.png \
     -o docs/screenshots/comparison_overlay.png \
     --alpha 0.5
   ```
   Or run directly via Python PIL:
   ```python
   from PIL import Image
   ref = Image.open("docs/screenshots/reference.png").convert("RGBA")
   dev = Image.open("docs/screenshots/device_screen.png").convert("RGBA").resize(ref.size, Image.LANCZOS)
   blend = Image.blend(ref, dev, 0.5)
   
   w, h = ref.size
   comp = Image.new("RGBA", (w * 3, h))
   comp.paste(ref, (0, 0))
   comp.paste(dev, (w, 0))
   comp.paste(blend, (w * 2, 0))
   comp.save("docs/screenshots/comparison_overlay.png")
   ```
3. **Multimodal `read_file` Inspection:**
   - Inspect `comparison_overlay.png` directly via multimodal vision.
   - Check if HUD capsules, board columns, chip diameters, and booster bars align perfectly without ghosting or double edges in the 50:50 blend.
   - Tune sub-pixel origin offsets or padding until ghosting is eliminated.

---

## 4. Verification & Gate Criteria (Checklist)
- [ ] UnityFS/APK assets decoded with zero third-party dependency breakage.
- [ ] 3D mesh vertices and height rings extracted and mathematically embedded into rendering code.
- [ ] Zero copyright infringement: all proprietary fonts and raw APK PNGs deleted; OFL font and custom-drawn 3D icons substituted.
- [ ] Full board mechanics and state management verified via unit tests (e.g., Rust `cargo test`).
- [ ] Physical device screenshot captured and verified via 50:50 alpha overlay with zero noticeable structural misalignment.
- [ ] All specs and QA reports permanently logged under `docs/`.
