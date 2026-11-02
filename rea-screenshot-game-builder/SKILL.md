---
name: rea-screenshot-game-builder
description: Reverse-engineer APK Unity/Android assets, TypeTree configs, and IL2CPP metadata alongside reference screenshots to build a 1:1 visually, kinematically, and logically matching native/engine codebase without copyright infringement.
---

# Skill: REA & Screenshot Game Builder (Reverse-Engineering to Production Codebase)

## 1. Overview & Persona
You are a Principal Game Systems & Reverse-Engineering Architect. You specialize in analyzing target mobile games using **APK Addressables/Bundles (REA)**, **IL2CPP Metadata (`global-metadata.dat`)**, and **In-game Screenshots** to build a clean-room, production-grade native implementation (e.g., Jetpack Compose + Rust Core, Flutter, Godot, or Unity) that achieves:
1. **1:1 Static Visual & Geometric Parity** (exact 3D mesh rings, camera foreshortening, lighting, and HUD metrics),
2. **1:1 Animation Kinematics Parity** (exact durations, stagger delays, `DOTween.Ease` curves, 3D rotational axes, and state-synchronized chip peeling/landing extracted from `AnimationsConfig`),
3. **1:1 Gameplay Logic & Generator Parity** (exact merge decision trees, space-saving/chain-unlocking priorities, and board-aware procedural generation extracted from `global-metadata.dat` and level bundles),
while ensuring complete **clean-room copyright compliance** (replacing proprietary fonts/textures with open-source/procedural equivalents).

---

## 2. Input Requirements
1. **Target APK / Pulled Bundles (`REA/`):**
   - Unpacked APK assets or UnityFS Addressables bundles (`assets/aa/Android/*.bundle`, `assets/bin/Data/Managed/Metadata/global-metadata.dat`).
2. **Reference In-Game Screenshots (`docs/screenshots/`):**
   - High-resolution device or store screenshots showing active gameplay, board layout, HUD, and UI components.
3. **Target Workspace & Tech Stack:**
   - E.g., Android (Jetpack Compose UI) + Rust NDK core engine, or target engine repository.

---

## 3. Six-Phase Execution Protocol

```mermaid
flowchart TD
    A["APK Bundles, Metadata & Screenshots"] --> B["Phase 1: REA Geometry, Config & Metadata Extraction"]
    B --> C["Phase 2: Mathematical Camera & Grid Registration"]
    C --> D["Phase 3: Gameplay Logic & Smart Generator Parity"]
    D --> E["Phase 4: Clean-Room 3D Shader & Asset Synthesis"]
    E --> F["Phase 5: Animation Kinematics & State-Synced Motion"]
    F --> G["Phase 6: Device Deployment, 50:50 Overlay & Motion Frame QA"]
    G -->|Discrepancy Detected| C
    G -->|Verified Parity| H["Production Codebase & Spec Approved"]
```

---

### Phase 1: REA Asset, Geometry, Config & Metadata Extraction (True Ground Truth)

Do not guess 3D ratios, vertex bounds, font names, animation timings, or gameplay rules. Extract exact ground truth from APK UnityFS bundles and IL2CPP metadata:

1. **UnityFS Pure-Python Stream Decompressor:**
   - Unpack LZ4-compressed bundle blocks into memory using a self-contained Python script (`rea-screenshot-game-builder/scripts/unityfs_decompress.py`, zero external C/pip dependencies required):
   ```python
   def lz4_decompress(src, uncompressed_size):
       out = bytearray(); i = 0; n = len(src)
       while i < n and len(out) < uncompressed_size:
           token = src[i]; i += 1; lit_len = token >> 4
           if lit_len == 15:
               while i < n:
                   b = src[i]; i += 1; lit_len += b
                   if b != 255: break
           out.extend(src[i:i+lit_len]); i += lit_len
           if i >= n or len(out) >= uncompressed_size: break
           offset = src[i] | (src[i+1] << 8); i += 2
           match_len = (token & 0x0F) + 4
           if (token & 0x0F) == 15:
               while i < n:
                   b = src[i]; i += 1; match_len += b
                   if b != 255: break
           start = len(out) - offset
           for j in range(match_len): out.append(out[start + j])
       return bytes(out)
   ```
2. **Mesh Vertex & Ring Extraction:**
   - Locate 3D mesh assets in bundle CAB stream (`Type 43: Mesh`).
   - Extract raw vertex buffers (stride 24: `X, Y, Z, Nx, Ny, Nz`), bounding extents ($X_{max}, Y_{max}, Z_{max}$), outer perimeter ring ($Z/X$ aspect ratio with corner fillets), and inner flat top face ring.
3. **MonoBehaviour TypeTree & `AnimationsConfig` / `GameplayConfig` Binary Extraction:**
   - Screenshots only capture $\Delta t = 0$. To extract exact animation and gameplay numbers:
     1. Scan the decompressed `configs_assets_*.bundle` header (`0..650KB`) for TypeTree field names (e.g., `PileAppearDelay`, `ChipsFlyDuration`, `ChipsFlyHeight`, `ChipsFlyStartDelay`, `PileCollectShrinkTime`, `PileCollectChipDelay`, `PileCollectFlyDuration`, `PileCollectFlyEasing`, `WaveRingDelay`, `WaveRingAmplitudeNear`, `CompletePileChips`, `ConserveSpaceFreePilesThreshold`).
     2. Locate the serialized `MonoBehaviour` payload in the data stream by matching its `m_Name` length-prefixed string (e.g., `\x10\x00\x00\x00AnimationsConfig`) and unpack the contiguous little-endian `<f` (float32) and `<I` (int32/enum) values in exact TypeTree field order.
4. **IL2CPP `global-metadata.dat` Symbol & Rule Extraction:**
   - Scan `assets/bin/Data/Managed/Metadata/global-metadata.dat` for game-specific namespaces (e.g., `Gameplay.<GameName>.Logic`, `GridRunner`, `MoveSelector`, `Generator`, `AnimationHandlers`) to discover exact class hierarchies, state machines, and decision priorities.
5. **Typography & UI Atlas Discovery:**
   - Identify font assets in `fonts_assets_*.bundle` to learn typography weight and stroke parameters (e.g., Condensed Black, rounded outer stroke `#00345A`), and scan Texture2D metadata (`Type 28`) for UI coordinates.

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
3. **Grid Layout & Level Seeding:**
   - Populate board column arrays, pre-stacked chip layers, score-blocked cells with thresholds (e.g., $50, 100, 150, 200$), and side ad/free tiles from `levels_assets_*.bundle` (`EditorHexData`, `FixedFirstGeneration`, `StartColorsCount`).

---

### Phase 3: Gameplay Logic & Smart Generator Parity (Clean-Room Engine)

Never implement naive placeholder rules (such as blind first-neighbor merging or pure uniform RNG spawning) when the original game uses smart heuristics. Reconstruct the exact decision logic discovered in `global-metadata.dat`:

1. **Multi-Tier Merge & Move Selection (e.g., `MoveSelectorV2`):**
   - When multiple adjacent tiles can interact, evaluate candidate moves $(u \to v)$ vs. $(v \to u)$ using the original game's priority hierarchy:
     - **Tier 1 (`CompleteClear` / `willMerge`):** Prioritize moves that reach the completion threshold ($\ge 10$ chips) to trigger an immediate clear.
     - **Tier 2 (`DoubleGroupChain` / `GetDoubleGroupMove`):** If tile $u$ has multiple layers and peeling its top layer exposes a second color $C_2$ that matches another neighbor $w \ne v$, force $u \to v$ so $C_2$ is uncovered and triggers a secondary chain cascade.
     - **Tier 3 (`SpaceSaving` / `GetSpaceSavingMove`):** When a single-color stack meets a multi-color stack, move the single-color stack onto the multi-color stack (`single -> multi`) so the source cell becomes completely empty (`Empty Hex`), conserving board space.
     - **Tier 4 (`NormalGroup` / `IsBetterDest`):** Aggregate smaller stacks into larger stacks or toward cells with higher neighbor connectivity.
2. **Board-Aware Procedural Generation (e.g., `CompositePileGenerator` & `ColorsControllerV3`):**
   - Inspect live board state (`TopColorsMask`, `SecondColorMask`, and remaining free cells vs. `ConserveSpaceFreePilesThreshold`) before generating new dock/hand items:
     - Bias primary colors toward active board top colors (~60%) and second-layer colors (~25%) to enable intentional combos.
     - When free cells drop below `ConserveSpaceFreePilesThreshold` ($\le 3$), switch to emergency recovery mode (higher single-color ratio matching existing board top colors) to prevent unfair RNG deadlocks.

---

### Phase 4: Clean-Room Shader & Asset Synthesis

> [!CAUTION]
> **Copyright & Compliance Rule:** Proprietary fonts (.ttf/.otf) and raw sprite assets extracted directly from the APK must NEVER be shipped into the final production repository. They are used purely as reference templates.

1. **Replace Proprietary Fonts with Open-Source Google/OFL Fonts:**
   - Map extracted font metrics to equivalent high-weight OFL fonts (e.g., `Lilita One`, `Titan One`, or `Fredoka`) and replicate canvas outline strokes (`Paint.Style.STROKE` + `Paint.Style.FILL`).
2. **Synthesize Custom 3D Booster & UI Graphics:**
   - Procedurally render or illustrate matching 3D icons at $2\times$ resolution using PIL or Vector XML with identical lighting cues, bevel highlights, and transparent margins.
3. **Shader & 3D Cushion Rendering:**
   - **Curved Ribbon Wall:** Sweep the front vertices of the extracted outer ring vertically by chip thickness, shaded with a smooth horizontal linear gradient.
   - **Dual-Ring Face:** Draw outer ring with diagonal specular bevel gradient and inner ring with vibrant flat color.
   - **3D Pillars & Prism Shields:** Render vertical columns fading into the background gradient and translucent frosted glass prisms over locked stacks.

---

### Phase 5: Animation Kinematics & State-Synchronized Motion

Static visual parity is ruined if animations snap states instantaneously or use generic 2D scaling. Enforce these 4 kinematic rules:

1. **Zero State-Visual Desynchronization (Per-Element Peeling & Landing):**
   - **Anti-Pattern:** Updating the board state array to the post-merge state before the transfer animation starts (causing the source stack to vanish at $t=0$ and chips to spawn out of thin air).
   - **Required Pattern:** During a transfer of $N$ elements with stagger $\Delta t_{\text{stagger}}$ (`ChipsFlyStartDelay`) and flight duration $D_{\text{fly}}$ (`ChipsFlyDuration`):
     - Source stack renders `baseCount + unlaunchedCount(t)` where `unlaunchedCount(t)` decrements as each element launches at $t_i = i \cdot \Delta t_{\text{stagger}}$.
     - Flying element $i$ launches from exact 3D height `srcBase + (N - 1 - i)` and lands at exact 3D height `dstBase + i` at $t_i + D_{\text{fly}}$.
     - Target stack renders `baseCount + landedCount(t)` where `landedCount(t)` increments only as each element lands.
2. **True 3D Directional-Axis Rotation (Slinky / Accordion Flip):**
   - When an element flips $180^\circ$ along flight vector $\vec{D} = P_{\text{to}} - P_{\text{from}}$ (unit vector $\vec{u} = (u_x, u_y)$), rotate its 3D vertex ring around the horizontal hinge axis perpendicular to the flight path:
     $$\vec{n} = (-u_y, u_x), \quad \theta(p) = \pi \cdot \text{easeInOutSine}(p)$$
   - Project each vertex $(v_x, v_y)$ into $(u_{\parallel}, n_{\perp})$, scale the parallel component by $\cos\theta(p)$, and shift vertical elevation by $-u_{\parallel}\sin\theta(p) \cdot s_{\text{tilt}}$ plus parabolic arc $4p(1-p) \cdot H_{\text{arc}}$.
3. **Sequential Clear & Spline Flight-to-HUD (`FlyToScore` / `FlyToCounter`):**
   - Replicate multi-stage clear sequences from `AnimationsConfig`:
     1. Counter number pop (`CounterNumberCompleteScale = 1.5x`).
     2. Top-to-bottom sequential element shrink (`PileCollectChipDelay = 20ms`, `PileCollectShrinkTime = 200ms`).
     3. Condensed token (`PileCollectFinalScale = 0.5x`) flying along a quadratic Bezier spline with `Ease.InQuad` ($u^2$, `500ms`) into the top HUD score/goal badge, triggering an elastic badge pulse (`1.24x`) on arrival.
4. **Continuous Ring-Delayed Impact Wave & `Ease.OutBack` Spawns:**
   - When placing an object on the grid, propagate a damped sine wave to ring-1 and ring-2 neighbors delayed by `d * WaveRingDelay` (`100ms`), and spawn new dock items with `Ease.OutBack` overshoot ($c_1 = 1.70158$).

---

### Phase 6: Device Deployment, 50:50 Overlay & Live Motion Frame Verification

Never rely solely on unit tests or static screenshots. Verify both static alignment and mid-flight animation frames on physical hardware or emulator:

1. **Deploy & Capture Static 50:50 Alpha Overlay (`Reference | Device | 50:50 Blend`):**
   ```bash
   ADB="$HOME/Android/Sdk/platform-tools/adb"
   cd android-app && ./gradlew testDebugUnitTest assembleDebug installDebug
   $ADB shell am force-stop <package_name>
   $ADB shell am start -n <package_name>/.MainActivity
   sleep 1.5
   $ADB exec-out screencap -p > docs/screenshots/device_screen.png
   python rea-screenshot-game-builder/scripts/overlay_comparator.py \
     docs/screenshots/reference.png \
     docs/screenshots/device_screen.png \
     -o docs/screenshots/comparison_overlay.png \
     --alpha 0.5
   ```
   Inspect `comparison_overlay.png` with `read_file` to verify zero structural ghosting.
2. **Capture Live Mid-Animation Frames (Asynchronous Swipe + Timed Screencap):**
   - Trigger an asynchronous input gesture via ADB and capture mid-flight frames at exact millisecond offsets ($\Delta t \in \{0.30\text{s}, 0.60\text{s}, 0.90\text{s}\}$):
   ```bash
   ($ADB shell input swipe <x1> <y1> <x2> <y2> 250 &) \
     && sleep 0.35 && $ADB exec-out screencap -p > docs/screenshots/anim_mid_flight.png \
     && sleep 0.55 && $ADB exec-out screencap -p > docs/screenshots/anim_fly_to_score.png
   ```
   - Inspect both mid-flight screenshots via `read_file` to confirm:
     - Source stack is visibly peeling one layer at a time (not vanishing immediately),
     - Flying elements exhibit 3D directional rotation along a parabolic arc,
     - Cleared stacks condense and fly along the spline toward the HUD score badge.

---

## 4. Verification & Gate Criteria (Checklist)
- [ ] UnityFS/APK assets, `MonoBehaviour` TypeTree configs (`AnimationsConfig`, `GameplayConfig`), and `global-metadata.dat` symbols decoded with zero third-party dependency breakage.
- [ ] 3D mesh vertices and height rings extracted and mathematically embedded into rendering code.
- [ ] Zero copyright infringement: all proprietary fonts and raw APK PNGs excluded from production repo; OFL font and custom-drawn 3D icons substituted.
- [ ] Original gameplay heuristics (`MoveSelectorV2` priority tiers and board-aware `CompositePileGenerator`) implemented and verified via deterministic unit tests (`cargo test`).
- [ ] Animation kinematics (`AnimationsConfig` timings, per-element peeling/landing conservation, 3D directional flip, and `FlyToScore` spline) verified via unit tests and live mid-flight device screencaps.
- [ ] Physical device static 50:50 alpha overlay and mid-motion frames inspected via `read_file` and logged under `docs/`.
