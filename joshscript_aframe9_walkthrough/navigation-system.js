/* navigation-system.js - restored original-like implementation for the walkthrough */

// Note: mapping controls are created by init() when CONFIG.SHOW_MAPPING_CONTROLS
// is true. Earlier iterations aggressively removed the panel at script-load;
// that behavior has been removed so pages can show the mapping UI again.

const CONFIG = {
    DATA_FILE: 'cone_data.json',
    PANORAMA_BASE_PATH: 'panoramas/',
    SPHERE_SIZE_DEFAULT: 0.0875,
    // If true, swap the Y and Z components read from cone.dxf_position
    // (some cone_data.json exports use Y as elevation and Z as lateral coords).
    // Default: true — user-selected working mapping sets Y/Z swap on by default
    FLIP_YZ_ON_LOAD: true,
    // Optional negation flags applied after swapping (or directly if no swap)
    NEGATE_Y_ON_LOAD: false,
    // Negate Z on load default (user selected mapping leaves this off)
    NEGATE_Z_ON_LOAD: false,
    // Vertical offset applied to all spheres in A-Frame meters (positive raises, negative lowers)
    SPHERE_Y_OFFSET: 0,
    // Step for elevation key adjustments (Q/E)
    ELEVATION_STEP: 0.1,
    // When true, ignore per-page mapping overrides and apply these global mapping defaults
    ENFORCE_GLOBAL_MAPPING: false,
    // POSITION_ROTATION: optional rotation to apply to all positions (axis: 'x'|'y'|'z', degrees: number)
};
// Control whether to show the runtime mapping controls panel
// Default: hidden — pages should explicitly opt-in to show controls
CONFIG.SHOW_MAPPING_CONTROLS = true;
// Default mapping choices matching user's confirmed selection
CONFIG.INVERT_Y_SIGN = true; // selected
CONFIG.INVERT_Z_SIGN = true; // selected
CONFIG.INVERT_X_SIGN = false; // selected OFF by user

// Allow per-page overrides via window.PAGE_CONFIG (set by index pages)
if (typeof window !== 'undefined' && window.PAGE_CONFIG && typeof window.PAGE_CONFIG === 'object') {
    const pc = window.PAGE_CONFIG;
    if (pc.DATA_FILE) CONFIG.DATA_FILE = pc.DATA_FILE;
    if (typeof pc.FLIP_YZ_ON_LOAD === 'boolean') CONFIG.FLIP_YZ_ON_LOAD = pc.FLIP_YZ_ON_LOAD;
    if (typeof pc.NEGATE_Y_ON_LOAD === 'boolean') CONFIG.NEGATE_Y_ON_LOAD = pc.NEGATE_Y_ON_LOAD;
    if (typeof pc.NEGATE_Z_ON_LOAD === 'boolean') CONFIG.NEGATE_Z_ON_LOAD = pc.NEGATE_Z_ON_LOAD;
    if (pc.PANORAMA_BASE_PATH) CONFIG.PANORAMA_BASE_PATH = pc.PANORAMA_BASE_PATH;
        if (typeof pc.REMOVE_SKY === 'boolean') CONFIG.REMOVE_SKY = pc.REMOVE_SKY;
        if (typeof pc.CAMERA_FLIP_UPDOWN === 'boolean') CONFIG.CAMERA_FLIP_UPDOWN = pc.CAMERA_FLIP_UPDOWN;
            if (typeof pc.INVERT_SKY_PITCH === 'boolean') CONFIG.INVERT_SKY_PITCH = pc.INVERT_SKY_PITCH;
            if (typeof pc.INVERT_SKY_ROLL === 'boolean') CONFIG.INVERT_SKY_ROLL = pc.INVERT_SKY_ROLL;
            if (typeof pc.SKY_ADD_180_Z === 'boolean') CONFIG.SKY_ADD_180_Z = pc.SKY_ADD_180_Z;
            // Allow flipping the DXF Y sign mapping (some exports have inverted elevation)
                if (typeof pc.INVERT_Y_SIGN === 'boolean') CONFIG.INVERT_Y_SIGN = pc.INVERT_Y_SIGN;
                if (typeof pc.INVERT_Z_SIGN === 'boolean') CONFIG.INVERT_Z_SIGN = pc.INVERT_Z_SIGN;
                    if (typeof pc.SHOW_MAPPING_CONTROLS === 'boolean') CONFIG.SHOW_MAPPING_CONTROLS = pc.SHOW_MAPPING_CONTROLS;
                if (typeof pc.INVERT_X_SIGN === 'boolean') CONFIG.INVERT_X_SIGN = pc.INVERT_X_SIGN;
        // MODE controls how pitch/roll are applied: 'full' (default), 'clamp_pitch', 'zero_pitch', 'yaw_only'
        if (pc.MODE) CONFIG.MODE = pc.MODE;
        if (typeof pc.CLAMP_PITCH_DEG === 'number') CONFIG.CLAMP_PITCH_DEG = pc.CLAMP_PITCH_DEG;
                    // Allow pages to set a default vertical offset for spheres (meters)
                    if (typeof pc.SPHERE_Y_OFFSET === 'number') CONFIG.SPHERE_Y_OFFSET = pc.SPHERE_Y_OFFSET;
    }

    // Optionally enforce a single global mapping across all pages so the user doesn't need
    // to toggle runtime controls on each page. When enabled, this will override any
    // per-page mapping flags (FLIP/NEGATE/INVERT and SHOW_MAPPING_CONTROLS).
    if (CONFIG.ENFORCE_GLOBAL_MAPPING) {
        const forced = {
            FLIP_YZ_ON_LOAD: false,
            NEGATE_Y_ON_LOAD: false,
            NEGATE_Z_ON_LOAD: true,
            INVERT_X_SIGN: true,
            INVERT_Y_SIGN: true,
            INVERT_Z_SIGN: true,
            SHOW_MAPPING_CONTROLS: false
        };
        Object.assign(CONFIG, forced);
        // Also ensure the page-level PAGE_CONFIG reflects the enforced mapping so
        // any other scripts reading window.PAGE_CONFIG see the same values.
        try {
            window.PAGE_CONFIG = Object.assign(window.PAGE_CONFIG || {}, forced);
        } catch (e) {
            /* ignore if window not available */
        }
        console.log('ENFORCE_GLOBAL_MAPPING active: mapping defaults enforced', forced);
        // Remove or hide any mapping-controls UI immediately so the user never
        // sees it and so no mapping change events can fire.
        (function enforceNoMappingControls() {
            function removePanel() {
                try {
                    const el = document.getElementById('mapping-controls');
                    if (el && el.parentElement) el.parentElement.removeChild(el);
                    // Remove any stray checkboxes with the 'mc_' id prefix
                    const mcs = document.querySelectorAll("[id^='mc_']");
                    mcs.forEach(n => n.parentElement && n.parentElement.removeChild(n));
                    // Inject CSS to forcibly hide the panel if created later
                    if (!document.getElementById('mapping-controls-hide-style')) {
                        const s = document.createElement('style');
                        s.id = 'mapping-controls-hide-style';
                        s.textContent = '#mapping-controls{display:none !important; visibility:hidden !important;} [id^="mc_"]{display:none !important;}';
                        (document.head || document.documentElement).appendChild(s);
                        console.log('Mapping controls hide-style injected');
                    }
                } catch (e) { /* ignore */ }
            }
            if (typeof document !== 'undefined') {
                // Try immediate removal (script may run after DOM exists)
                removePanel();
                // Also ensure removal after DOMContentLoaded
                document.addEventListener('DOMContentLoaded', removePanel);
            }
        })();
    }

// Example: set CONFIG.POSITION_ROTATION = { axis: 'z', degrees: 90 } to rotate all positions around Z by 90°

function rotatePointAroundOrigin(p, axis, degrees) {
    if (!p || typeof degrees !== 'number') return p;
    const rad = degrees * (Math.PI / 180);
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    let x = p.x || 0;
    let y = p.y || 0;
    let z = p.z || 0;
    let rx = x, ry = y, rz = z;
    switch ((axis || '').toLowerCase()) {
        case 'z':
            rx = x * cos - y * sin;
            ry = x * sin + y * cos;
            rz = z;
            break;
        case 'y':
            rx = x * cos + z * sin;
            ry = y;
            rz = -x * sin + z * cos;
            break;
        case 'x':
            rx = x;
            ry = y * cos - z * sin;
            rz = y * sin + z * cos;
            break;
        default:
            return p;
    }
    return { x: rx, y: ry, z: rz };
}

function getSphereYOffset() {
    return (typeof CONFIG.SPHERE_Y_OFFSET === 'number') ? CONFIG.SPHERE_Y_OFFSET : 0;
}

// Map a raw DXF position into A-Frame coordinates according to the current CONFIG.
function mapPositionToAframe(pos) {
    if (!pos) return { x: 0, y: 0, z: 0 };
    let x = pos.x || 0;
    let y = pos.y || 0;
    let z = pos.z || 0;
    // Apply swap of Y/Z if requested
    if (CONFIG.FLIP_YZ_ON_LOAD) {
        const tmp = y; y = z; z = tmp;
    }
    // Apply optional negations
    if (CONFIG.NEGATE_Y_ON_LOAD) y = -y;
    if (CONFIG.NEGATE_Z_ON_LOAD) z = -z;
    // Apply sign inversions used to map DXF axes into A-Frame
    const ax = CONFIG.INVERT_X_SIGN ? -x : x;
    const ay = CONFIG.INVERT_Y_SIGN ? y : -y;
    const az = CONFIG.INVERT_Z_SIGN ? -z : z;
    return { x: ax, y: ay, z: az };
}

// Map a raw DXF direction vector into a THREE.Vector3 in A-Frame coords
function mapDirVecToAframe(v) {
    if (!v) return new THREE.Vector3(0, 0, 1);
    const m = mapPositionToAframe({ x: v.x || 0, y: v.y || 0, z: v.z || 0 });
    return new THREE.Vector3(m.x, m.y, m.z);
}

let state = {
    cones: [],
    currentCone: null
    , userElev: 0
};
// session state for sky rotation (degrees)
state.skyYawOffset = 0;

function normalizePanoramaPath(path) {
    if (!path) return '';
    path = path.replace(/^\.\//, '').replace(/^\//, '');
    if (path.startsWith(CONFIG.PANORAMA_BASE_PATH)) return path.replace(/\\/g, '/');
    return (CONFIG.PANORAMA_BASE_PATH + path).replace(/\\/g, '/');
}

async function loadConeData() {
    const r = await fetch(CONFIG.DATA_FILE);
    if (!r.ok) throw new Error('Failed to fetch ' + CONFIG.DATA_FILE);
    const data = await r.json();
    state.cones = data.cones || data.cameras || [];
    // Debug: show first cone position before any fix
    if (state.cones && state.cones.length > 0) {
        const p0 = state.cones[0].dxf_position || state.cones[0].position || {};
        console.log('First cone original dxf_position:', JSON.stringify(p0));
    }
    // NOTE: Do not mutate the raw cone positions/directions here. Mapping transforms
    // (swap/negate/invert) should be applied consistently in one place so that
    // runtime mapping controls and page-level defaults produce identical results.
    // Raw positions are preserved and stored on each cone as _orig_position; mapping
    // will be applied later in applyPositionMapping().

    // If requested, hide the skybox element and set a neutral scene background
    if (CONFIG.REMOVE_SKY) {
        const skyEl = document.getElementById('panorama-sky');
        try {
            if (skyEl) skyEl.setAttribute('visible', 'false');
            const scene = document.querySelector('a-scene');
            if (scene) scene.setAttribute('background', { color: '#666' });
            console.log('REMOVE_SKY enabled: sky hidden and scene background set');
        } catch (e) {
            console.warn('Failed to hide sky element', e);
        }
    } else {
        // Ensure the sky is visible and the scene background is cleared when NOT removing sky
        const skyEl = document.getElementById('panorama-sky');
        try {
            if (skyEl) skyEl.setAttribute('visible', 'true');
            const scene = document.querySelector('a-scene');
            if (scene) scene.setAttribute('background', null);
            console.log('REMOVE_SKY disabled: sky shown and scene background cleared');
        } catch (e) {
            /* ignore */
        }
    }
    // Optionally rotate positions around origin to correct building orientation
    if (CONFIG.POSITION_ROTATION && CONFIG.POSITION_ROTATION.axis && typeof CONFIG.POSITION_ROTATION.degrees === 'number') {
        const { axis, degrees } = CONFIG.POSITION_ROTATION;
        console.log(`Applying POSITION_ROTATION axis=${axis} degrees=${degrees}`);
        state.cones.forEach((cone) => {
            const p = cone.dxf_position || cone.position;
            if (p) {
                const before = { x: p.x, y: p.y, z: p.z };
                const rotated = rotatePointAroundOrigin(p, axis, degrees);
                p.x = rotated.x; p.y = rotated.y; p.z = rotated.z;
                // Rotate the direction vectors as well (if present)
                if (cone.direction) {
                    if (cone.direction.forward) {
                        const f = cone.direction.forward;
                        const rf = rotatePointAroundOrigin({ x: f.x, y: f.y, z: f.z }, axis, degrees);
                        f.x = rf.x; f.y = rf.y; f.z = rf.z;
                    }
                    if (cone.direction.up) {
                        const u = cone.direction.up;
                        const ru = rotatePointAroundOrigin({ x: u.x, y: u.y, z: u.z }, axis, degrees);
                        u.x = ru.x; u.y = ru.y; u.z = ru.z;
                    }
                }
            }
        });
    }
    // Debug: show first cone position after flipping
    if (state.cones && state.cones.length > 0) {
        const p0b = state.cones[0].dxf_position || state.cones[0].position || {};
        console.log('First cone dxf_position after FLIP_YZ_ON_LOAD:', JSON.stringify(p0b));
    }
    // Make the first cone the observer origin and convert all cone positions to be relative
    if (state.cones && state.cones.length > 0) {
        const first = state.cones[0];
        const base = (first.dxf_position || first.position);
        if (base && typeof base.x === 'number') {
            console.log('Using first cone as observer origin (base raw):', JSON.stringify(base));
            state.cones.forEach((cone, idx) => {
                const p = cone.dxf_position || cone.position;
                if (!p) return;
                // preserve original absolute position (raw, unmodified)
                cone._orig_position = { x: p.x, y: p.y, z: p.z };
                // compute and store relative raw position (origin = first cone)
                cone._rel_dxf_position = { x: p.x - base.x, y: p.y - base.y, z: p.z - base.z };
            });
            console.log('First cone relative raw position:', JSON.stringify(state.cones[0]._rel_dxf_position));
            // Store base A-Frame Y using the mapping helper so camera Y is consistent
            const mappedBase = mapPositionToAframe(base);
            state.baseAframeY = mappedBase.y;
            console.log('Base A-Frame Y (camera eye height):', state.baseAframeY);
        } else {
            console.warn('First cone has no numeric position; skipping origin-relative conversion');
        }
    }
    const totalEl = document.getElementById('total-cones');
    if (totalEl) totalEl.textContent = (state.cones.length || 0);
    return data;
}

function createSphereForCone(cone, idx) {
    const container = document.getElementById('spheres-container');
    const sphere = document.createElement('a-sphere');
    sphere.setAttribute('class', 'clickable nav-sphere');
    sphere.setAttribute('radius', CONFIG.SPHERE_SIZE_DEFAULT);
    // Use applied mapped position (if available) or compute mapping from raw relative position
    // Ensure cone._appliedPos is the canonical mapped position (no display-only offsets)
    let basePos = cone._appliedPos;
    if (!basePos) {
        const baseRaw = (state.cones && state.cones.length > 0) ? (state.cones[0]._orig_position || state.cones[0].dxf_position) : null;
        if (baseRaw) {
            const mappedBase = mapPositionToAframe(baseRaw);
            const mappedThis = mapPositionToAframe(cone._orig_position || cone._rel_dxf_position || { x: 0, y: 0, z: 0 });
            basePos = { x: mappedThis.x - mappedBase.x, y: mappedThis.y - mappedBase.y, z: mappedThis.z - mappedBase.z };
        } else {
            basePos = mapPositionToAframe(cone._rel_dxf_position || cone._orig_position || { x: 0, y: 0, z: 0 });
        }
        cone._appliedPos = basePos;
    }
    // Display the sphere with the visual vertical offset applied
    const dispY = basePos.y + getSphereYOffset();
    sphere.setAttribute('position', `${basePos.x} ${dispY} ${basePos.z}`);
    sphere.addEventListener('click', () => navigateToCone(cone));
    container.appendChild(sphere);
    cone._sphere = sphere;
}

function updateAllSpheresPositions() {
    const baseRaw = (state.cones && state.cones.length > 0) ? (state.cones[0]._orig_position || state.cones[0].dxf_position) : null;
    const mappedBase = baseRaw ? mapPositionToAframe(baseRaw) : null;
    const sphereOffset = getSphereYOffset();
    state.cones.forEach((cone) => {
        if (!cone) return;
        let basePos = cone._appliedPos;
        if (!basePos) {
            if (mappedBase) {
                const mappedThis = mapPositionToAframe(cone._rel_dxf_position || cone._orig_position || { x: 0, y: 0, z: 0 });
                basePos = { x: mappedThis.x - mappedBase.x, y: mappedThis.y - mappedBase.y, z: mappedThis.z - mappedBase.z };
            } else {
                basePos = mapPositionToAframe(cone._rel_dxf_position || cone._orig_position || { x: 0, y: 0, z: 0 });
            }
            cone._appliedPos = basePos;
        }
        if (cone._sphere) cone._sphere.setAttribute('position', `${basePos.x} ${basePos.y + sphereOffset} ${basePos.z}`);
    });
}

// Debug helpers (top-level so init() can call them)
function ensureDebugMarkers() {
    const scene = document.querySelector('a-scene');
    if (!scene) return;
    // Origin marker: small red box at 0,0,0
    if (!document.getElementById('origin-marker')) {
        const box = document.createElement('a-box');
        box.setAttribute('id', 'origin-marker');
        box.setAttribute('position', '0 0 0');
        box.setAttribute('depth', '0.1'); box.setAttribute('height', '0.1'); box.setAttribute('width', '0.1');
        box.setAttribute('color', '#f00'); box.setAttribute('opacity', '0.9');
        scene.appendChild(box);
    }
    // Eye marker: small green sphere at camera eye height
    if (!document.getElementById('eye-marker')) {
        const s = document.createElement('a-sphere');
        s.setAttribute('id', 'eye-marker');
        s.setAttribute('radius', '0.06');
        s.setAttribute('color', '#0f0');
        scene.appendChild(s);
    }
}

function updateEyeMarker() {
    const s = document.getElementById('eye-marker');
    if (!s) return;
    // Compute the camera's world Y: camera local Y (baseAframeY) + rig Y + user elevation
    const camLocalY = (typeof state.baseAframeY === 'number') ? state.baseAframeY : 1.6;
    const rigY = (state.currentCone && state.currentCone._appliedPos) ? state.currentCone._appliedPos.y : 0;
    const userElev = (typeof state.userElev === 'number') ? state.userElev : 0;
    const worldEyeY = camLocalY + rigY + userElev;
    s.setAttribute('position', `0 ${worldEyeY} 0`);
}


async function populateScene() {
    const container = document.getElementById('spheres-container');
    container.innerHTML = '';
    state.cones.forEach((c, i) => createSphereForCone(c, i));
    // Apply any current mapping logic immediately so spheres show in the mapped positions
    applyPositionMapping();
}

// Recalculate applied positions from original absolute positions and current CONFIG toggles
function applyPositionMapping() {
    if (!state.cones || state.cones.length === 0) return;
    const first = state.cones[0];
    const base = first._orig_position || (first.dxf_position || first.position);
    if (!base) return;
    // compute applied positions for each cone using the mapping helper and update spheres
    const mappedBase = mapPositionToAframe(base);
    const sphereOffset = getSphereYOffset();
    state.cones.forEach((cone) => {
        const o = cone._orig_position || (cone.dxf_position || cone.position || { x: 0, y: 0, z: 0 });
        const mappedO = mapPositionToAframe(o);
        // The applied position is the mapped position relative to the mapped base
        const aframeX = mappedO.x - mappedBase.x;
        const aframeY = mappedO.y - mappedBase.y;
        const aframeZ = mappedO.z - mappedBase.z;
        // Store canonical applied position (no visual offset)
        cone._appliedPos = { x: aframeX, y: aframeY, z: aframeZ };
        // Update sphere display position using visual offset
        if (cone._sphere) cone._sphere.setAttribute('position', `${aframeX} ${aframeY + sphereOffset} ${aframeZ}`);
    });
    // Update rig to current cone if selected, or put at origin for first cone
    const rig = document.getElementById('camera-rig');
    const userElev = (typeof state.userElev === 'number') ? state.userElev : 0;
    if (state.currentCone) {
        const rel = state.currentCone._appliedPos;
        if (rig && rel) rig.setAttribute('position', `${rel.x} ${rel.y + userElev} ${rel.z}`);
    } else {
        if (rig) rig.setAttribute('position', `0 ${userElev} 0`);
    }
    // update debug eye marker
    updateEyeMarker();
    // If mapping controls are disabled globally or for this page, remove any existing panel
    if (!CONFIG.SHOW_MAPPING_CONTROLS) {
        const existing = document.getElementById('mapping-controls');
        if (existing && existing.parentElement) existing.parentElement.removeChild(existing);
    }
    // Recalculate sky orientation for the current cone so mapping toggles update panorama
    if (state.currentCone && state.currentCone.direction) {
        try { applySkyRotation(state.currentCone.direction); } catch (e) { /* ignore */ }
    }
}

function setCurrentConeUI(cone) {
    const el = document.getElementById('current-cone-id');
    if (el) el.textContent = cone.cone_id || cone.id || '';
}

async function navigateToCone(cone) {
    if (!cone) return;
    state.currentCone = cone;
    setCurrentConeUI(cone);
    const rig = document.getElementById('camera-rig');
    // Use the mapped/applied positions so any SPHERE_Y_OFFSET or mapping toggles
    // are respected for both spheres and the camera rig. applyPositionMapping()
    // will compute _appliedPos for the cone and set the rig accordingly.
    applyPositionMapping();
    try {
        await loadPanorama(cone.image_path || cone.filename || cone.image || '');
        if (cone.direction) {
            applySkyRotation(cone.direction);
            // Set camera rotation so it faces the horizon: inverse pitch applied by the sky
            const cam = document.getElementById('main-camera');
            if (cam) {
                // compute euler the same way applySkyRotation does
                let yaw = 0, pitch = 0, roll = 0;
                if (cone.direction.forward && cone.direction.up) {
                    const forward = new THREE.Vector3(cone.direction.forward.x, cone.direction.forward.z, -cone.direction.forward.y).normalize();
                    const up = new THREE.Vector3(-cone.direction.up.x, -cone.direction.up.z, cone.direction.up.y).normalize();
                    const right = new THREE.Vector3().crossVectors(up, forward).normalize();
                    const correctedUp = new THREE.Vector3().crossVectors(forward, right).normalize();
                    const rotMatrix = new THREE.Matrix4();
                    rotMatrix.set(
                        right.x, correctedUp.x, -forward.x, 0,
                        right.y, correctedUp.y, -forward.y, 0,
                        right.z, correctedUp.z, -forward.z, 0,
                        0, 0, 0, 1
                    );
                    const euler = new THREE.Euler().setFromRotationMatrix(rotMatrix, 'YXZ');
                    pitch = euler.x * (180 / Math.PI);
                    yaw = euler.y * (180 / Math.PI) + 90;
                    roll = -(euler.z * (180 / Math.PI));
                }
                // Camera rotation should be the inverse of the sky pitch/roll to look level
                // Ensure the camera local Y is set to the base eye height so the camera
                // doesn't drop to 0 after panorama load. This avoids a visible jump.
                const camY = (typeof state.baseAframeY === 'number') ? state.baseAframeY : 1.6;
                cam.setAttribute('position', `0 ${camY} 0`);
                console.log('navigateToCone: camera local Y set to', camY);
                // Camera rotation: invert the sky pitch and roll so the view is level relative to the panorama
                const invPitch = Number.isFinite(pitch) ? (pitch) : 0;
                const invRoll = Number.isFinite(roll) ? (-roll) : 0;
                // Default camera rotation: inverse of sky pitch/roll
                let camRotX = invPitch;
                let camRotY = 0;
                let camRotZ = invRoll;
                // Per-page override: flip camera up/down (hard flip) if requested
                if (CONFIG.CAMERA_FLIP_UPDOWN) {
                    // Set a clear flip to invert the view; easier to reason about than adding 180 to roll
                    cam.setAttribute('rotation', `0 0 180`);
                    console.log('CAMERA_FLIP_UPDOWN active: camera rotation set to 0 0 180');
                } else {
                    cam.setAttribute('rotation', `${camRotX} ${camRotY} ${camRotZ}`);
                }
            }
        }
    } catch (e) {
        console.warn('Failed to load panorama for cone', e);
    }
}

function loadPanorama(imagePath) {
    return new Promise((resolve, reject) => {
        const sky = document.getElementById('panorama-sky');
        const imgPathNorm = (imagePath || '').replace(/^\.\//, '').replace(/^\//, '');
        const full = imgPathNorm.startsWith(CONFIG.PANORAMA_BASE_PATH) ? imgPathNorm : (CONFIG.PANORAMA_BASE_PATH + imgPathNorm);
        const img = new Image(); img.crossOrigin = 'anonymous';
        img.onload = () => {
            if (sky) sky.setAttribute('src', full);
            // Reset camera pitch to horizon (avoid looking at floor on first load)
            const cam = document.getElementById('main-camera');
                if (cam) {
                    cam.setAttribute('rotation', '0 0 0');
                    const camY = (typeof state.baseAframeY === 'number') ? state.baseAframeY : 1.6;
                    cam.setAttribute('position', `0 ${camY} 0`);
                    console.log('loadPanorama: camera position set to baseAframeY', camY);
                }
            resolve(full);
        };
        img.onerror = () => reject(new Error('Failed to load ' + full));
        img.src = full;
    });
}

function rotateSkyBy(deg) {
    const sky = document.getElementById('panorama-sky');
    if (!sky) return;
    // Read current rotation (A-Frame may return string or object)
    let rot = sky.getAttribute('rotation');
    if (!rot) rot = { x: 0, y: 0, z: 0 };
    let y = 0;
    if (typeof rot === 'string') {
        const parts = rot.split(' ').map(Number);
        y = parts.length >= 2 ? parts[1] : 0;
    } else {
        y = rot.y || 0;
    }
    // Persist the offset in state so subsequent applySkyRotation calls include it
    state.skyYawOffset = ((state.skyYawOffset || 0) + deg) % 360;
    const newY = (y + deg) % 360;
    sky.setAttribute('rotation', { x: 0, y: newY, z: 0 });
    console.log(`rotateSkyBy: deg=${deg} currentYaw=${y} newYaw=${newY} storedOffset=${state.skyYawOffset}`);
}

// Rotate sky around specified axis ('x','y','z') by degrees.
function rotateSkyAxis(axis, deg) {
    const sky = document.getElementById('panorama-sky');
    if (!sky) return;
    // Read current rotation
    let rot = sky.getAttribute('rotation') || { x: 0, y: 0, z: 0 };
    let cx = 0, cy = 0, cz = 0;
    if (typeof rot === 'string') {
        const parts = rot.split(' ').map(Number);
        cx = parts[0] || 0; cy = parts[1] || 0; cz = parts[2] || 0;
    } else {
        cx = rot.x || 0; cy = rot.y || 0; cz = rot.z || 0;
    }

    let nx = cx, ny = cy, nz = cz;
    switch ((axis || 'y').toLowerCase()) {
        case 'x': nx = (cx + deg) % 360; break;
        case 'y': ny = (cy + deg) % 360; break;
        case 'z': nz = (cz + deg) % 360; break;
    }

    // If rotating Y, keep existing session offset logic
    if ((axis || 'y').toLowerCase() === 'y') {
        // reuse rotateSkyBy behavior
        rotateSkyBy(deg);
        return;
    }

    sky.setAttribute('rotation', { x: nx, y: ny, z: nz });
    console.log(`rotateSkyAxis: axis=${axis} deg=${deg} -> rotation=${nx} ${ny} ${nz}`);
}

function applySkyRotation(direction) {
    const sky = document.getElementById('panorama-sky');
    if (!sky || !direction) return;
    let yaw = 0, pitch = 0, roll = 0;
    if (direction.forward && direction.up) {
        // Map direction vectors into A-Frame coordinate space according to the mapping
        const forward = mapDirVecToAframe(direction.forward).normalize();
        const up = mapDirVecToAframe(direction.up).normalize();
        const right = new THREE.Vector3().crossVectors(up, forward).normalize();
        const correctedUp = new THREE.Vector3().crossVectors(forward, right).normalize();
        const rotMatrix = new THREE.Matrix4();
        rotMatrix.set(
            right.x, correctedUp.x, -forward.x, 0,
            right.y, correctedUp.y, -forward.y, 0,
            right.z, correctedUp.z, -forward.z, 0,
            0, 0, 0, 1
        );
        const euler = new THREE.Euler().setFromRotationMatrix(rotMatrix, 'YXZ');
        pitch = euler.x * (180 / Math.PI);
        yaw = euler.y * (180 / Math.PI) + 90;
        roll = -(euler.z * (180 / Math.PI));
    } else if (direction.x !== undefined) {
        const dir = new THREE.Vector3(direction.x, direction.z, -direction.y).normalize();
        yaw = Math.atan2(dir.x, dir.z) * (180 / Math.PI);
        pitch = -Math.asin(Math.max(-1, Math.min(1, dir.y))) * (180 / Math.PI);
    }
    // Apply pitch and roll as well so the horizon is centered in the panorama.
    // Snap yaw to 90° increments (keeps orientation tidy) but preserve pitch/roll.
    const snappedYaw = Math.round(yaw / 90) * 90;
    let totalYaw = (snappedYaw + (state.skyYawOffset || 0)) % 360;
    if (CONFIG.CAMERA_FLIP_UPDOWN) {
        totalYaw = (totalYaw + 180) % 360;
        console.log('CAMERA_FLIP_UPDOWN active: adding 180° yaw to sky to match camera flip');
    }
    // Ensure pitch/roll are finite numbers and clamp sensible ranges for X (pitch)
    let safePitch = Number.isFinite(pitch) ? pitch : 0;
    let safeRoll = Number.isFinite(roll) ? roll : 0;
    // Allow per-page inversions for experimentation
    if (CONFIG.INVERT_SKY_PITCH) { safePitch = -safePitch; console.log('INVERT_SKY_PITCH active: inverting pitch'); }
    if (CONFIG.INVERT_SKY_ROLL) { safeRoll = -safeRoll; console.log('INVERT_SKY_ROLL active: inverting roll'); }
    if (CONFIG.SKY_ADD_180_Z) { safeRoll = (safeRoll + 180) % 360; console.log('SKY_ADD_180_Z active: adding 180° to roll'); }
    // A-Frame sky rotation: x = -pitch (to align), y = yaw, z = roll
    sky.setAttribute('rotation', { x: -safePitch, y: totalYaw, z: safeRoll });
    console.log(`Sky rotation applied: yaw=${yaw.toFixed(2)} snapped=${snappedYaw} offset=${state.skyYawOffset||0} -> totalYaw=${totalYaw}, pitch=${safePitch.toFixed(2)}, roll=${safeRoll.toFixed(2)}`);
}

function wireUI() {
    const toggle = document.getElementById('sphere-toggle');
    if (toggle) toggle.addEventListener('change', () => document.getElementById('spheres-container').style.display = toggle.checked ? '' : 'none');
    const size = document.getElementById('sphere-size');
    if (size) size.addEventListener('input', () => document.querySelectorAll('.nav-sphere').forEach(s => s.setAttribute('radius', size.value)));
    const elevation = document.getElementById('sphere-elevation');
    if (elevation) elevation.addEventListener('input', () => document.querySelectorAll('.nav-sphere').forEach((s, i) => {
        const c = state.cones[i]; if (!c) return;
        const abs = c.dxf_position || c.position || c;
        const rel = c._rel_dxf_position || abs || { x: 0, y: 0, z: 0 };
        const ey = CONFIG.INVERT_Y_SIGN ? rel.y : -rel.y;
        const ez = CONFIG.INVERT_Z_SIGN ? -rel.z : rel.z;
        const ex = CONFIG.INVERT_X_SIGN ? -rel.x : rel.x;
        s.setAttribute('position', `${ex} ${ez + parseFloat(elevation.value)} ${ey}`);
    }));
    const exportBtn = document.getElementById('export-data'); if (exportBtn) exportBtn.addEventListener('click', () => {
        if (!state.cones || state.cones.length === 0) return alert('No data to export');
        const blob = new Blob([JSON.stringify({ cones: state.cones }, null, 2)], { type: 'application/json' });
        const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'cone_data_export.json'; a.click(); URL.revokeObjectURL(a.href);
    });
    const reset = document.getElementById('reset-view'); if (reset) reset.addEventListener('click', () => {
        // Reset rig/camera and clear any user elevation adjustments
        state.userElev = 0;
        applyPositionMapping();
        const rig = document.getElementById('camera-rig');
        if (rig) rig.setAttribute('position', '0 0 0');
        const cam = document.getElementById('main-camera');
        if (cam) {
            cam.setAttribute('rotation', '0 0 0');
            const camY = (typeof state.baseAframeY === 'number') ? state.baseAframeY : 1.6;
            cam.setAttribute('position', `0 ${camY} 0`);
        }
        updateEyeMarker();
    });
    const rotateBtn = document.getElementById('rotate-sky');
    if (rotateBtn) rotateBtn.addEventListener('click', () => rotateSkyBy(90));
    const rotateXBtn = document.getElementById('rotate-sky-x');
    if (rotateXBtn) rotateXBtn.addEventListener('click', () => rotateSkyAxis('x', 90));
    const rotateZBtn = document.getElementById('rotate-sky-z');
    if (rotateZBtn) rotateZBtn.addEventListener('click', () => rotateSkyAxis('z', 90));

    const resetSkyBtn = document.getElementById('reset-sky');
    if (resetSkyBtn) resetSkyBtn.addEventListener('click', () => {
        state.skyYawOffset = 0;
        const sky = document.getElementById('panorama-sky');
        if (sky) sky.setAttribute('rotation', { x: 0, y: 0, z: 0 });
        console.log('Sky rotation reset to 0 (offset cleared)');
    });

    // Keyboard shortcuts
    window.addEventListener('keydown', (ev) => {
        // Don't intercept keys while typing into inputs/textareas
        const targ = ev.target || document.activeElement;
        if (targ && (targ.tagName === 'INPUT' || targ.tagName === 'TEXTAREA' || targ.isContentEditable)) return;
        // Rotate sky
        if (ev.key === 'r' || ev.key === 'R') { rotateSkyBy(90); return; }
        if (ev.key === 'x' || ev.key === 'X') { rotateSkyAxis('x', 90); return; }
        if (ev.key === 'z' || ev.key === 'Z') { rotateSkyAxis('z', 90); return; }
        // Elevation keys: 'E' increases elevation, 'Q' decreases
        const step = (typeof CONFIG.ELEVATION_STEP === 'number') ? CONFIG.ELEVATION_STEP : 0.1;
        const actualStep = ev.shiftKey ? (step * 5) : step;
        if (ev.key === 'e' || ev.key === 'E') {
            state.userElev = (state.userElev || 0) + actualStep;
            console.log(`Elevation: +${actualStep} -> ${state.userElev}`);
            applyPositionMapping(); updateEyeMarker();
            return;
        }
        if (ev.key === 'q' || ev.key === 'Q') {
            state.userElev = (state.userElev || 0) - actualStep;
            console.log(`Elevation: -${actualStep} -> ${state.userElev}`);
            applyPositionMapping(); updateEyeMarker();
            return;
        }
    });
}

// Create a small on-screen panel with mapping toggles so the user can experiment live
function createMappingControls() {
    // If global enforcement is active, do not create mapping controls at all.
    if (CONFIG.ENFORCE_GLOBAL_MAPPING) {
        console.log('createMappingControls: blocked by ENFORCE_GLOBAL_MAPPING');
        const existing = document.getElementById('mapping-controls');
        if (existing && existing.parentElement) existing.parentElement.removeChild(existing);
        return;
    }
    if (document.getElementById('mapping-controls')) return;
    const panel = document.createElement('div');
    panel.id = 'mapping-controls';
    panel.style.position = 'fixed';
    panel.style.right = '8px';
    panel.style.top = '8px';
    panel.style.background = 'rgba(255,255,255,0.9)';
    panel.style.padding = '8px';
    panel.style.zIndex = '1000';
    panel.style.fontSize = '12px';
    panel.style.maxWidth = '200px';
    panel.style.borderRadius = '6px';
    panel.innerHTML = `<div style="font-weight:700;margin-bottom:6px">Mapping controls</div>`;

    const checks = [
        ['FLIP_YZ_ON_LOAD','Swap Y/Z'],
        ['NEGATE_Y_ON_LOAD','Negate Y'],
        ['NEGATE_Z_ON_LOAD','Negate Z'],
        ['INVERT_X_SIGN','Invert X'],
        ['INVERT_Y_SIGN','Invert Y'],
        ['INVERT_Z_SIGN','Invert Z']
    ];

    checks.forEach(([key, label]) => {
        const id = 'mc_' + key;
        const row = document.createElement('div');
        row.style.marginBottom = '4px';
        const cb = document.createElement('input'); cb.type = 'checkbox'; cb.id = id;
        cb.checked = !!CONFIG[key];
        cb.addEventListener('change', () => {
            if (CONFIG.ENFORCE_GLOBAL_MAPPING) {
                console.log(`Mapping control ignored (ENFORCE_GLOBAL_MAPPING): ${key}`);
                // Reset UI to the enforced value
                cb.checked = !!CONFIG[key];
                return;
            }
            CONFIG[key] = cb.checked;
            console.log(`Mapping control: ${key} -> ${CONFIG[key]}`);
            applyPositionMapping();
        });
        const lab = document.createElement('label'); lab.htmlFor = id; lab.style.marginLeft = '6px'; lab.textContent = label;
        row.appendChild(cb); row.appendChild(lab);
        panel.appendChild(row);
    });

    // Add a numeric input to control vertical offset (meters)
    const offsetRow = document.createElement('div');
    offsetRow.style.marginBottom = '6px';
    const offsetLabel = document.createElement('label');
    offsetLabel.htmlFor = 'mc_SPHERE_Y_OFFSET';
    offsetLabel.textContent = 'Vertical offset (m):';
    const offsetInput = document.createElement('input');
    offsetInput.type = 'number'; offsetInput.id = 'mc_SPHERE_Y_OFFSET'; offsetInput.step = '0.1';
    offsetInput.value = String(getSphereYOffset());
    offsetInput.style.marginLeft = '6px'; offsetInput.style.width = '60px';
    offsetInput.addEventListener('change', () => {
        if (CONFIG.ENFORCE_GLOBAL_MAPPING) { offsetInput.value = String(getSphereYOffset()); return; }
        CONFIG.SPHERE_Y_OFFSET = Number(offsetInput.value) || 0;
        console.log(`Mapping control: SPHERE_Y_OFFSET -> ${CONFIG.SPHERE_Y_OFFSET}`);
        applyPositionMapping();
    });
    offsetRow.appendChild(offsetLabel); offsetRow.appendChild(offsetInput); panel.appendChild(offsetRow);

    const btnRow = document.createElement('div'); btnRow.style.marginTop = '6px';
    const applyBtn = document.createElement('button'); applyBtn.textContent = 'Reapply mapping'; applyBtn.style.width = '100%';
    applyBtn.addEventListener('click', () => { applyPositionMapping(); });
    btnRow.appendChild(applyBtn);
    panel.appendChild(btnRow);

    document.body.appendChild(panel);
}

async function init() {
    try {
        await loadConeData();
        await populateScene();
        wireUI();
        // Only create mapping controls if explicitly requested by the page
        if (CONFIG.SHOW_MAPPING_CONTROLS) createMappingControls();
        if (state.cones && state.cones.length > 0) {
            // Place the camera rig at the observer origin (first cone) initially
            const rig = document.getElementById('camera-rig');
            const cam = document.getElementById('main-camera');
            if (rig) rig.setAttribute('position', '0 0 0');
            // Set camera Y to baseAframeY so the eye sits at the first cone's elevation
            if (cam && typeof state.baseAframeY === 'number') {
                cam.setAttribute('position', `0 ${state.baseAframeY} 0`);
            }
            ensureDebugMarkers(); updateEyeMarker();
            navigateToCone(state.cones[0]);
        }
    } catch (e) { console.error('Navigation init failed', e); }
}

document.addEventListener('DOMContentLoaded', init);

// Print the active mapping configuration so the page loads with visible confirmation
console.log('Active mapping CONFIG:', JSON.stringify({
    FLIP_YZ_ON_LOAD: CONFIG.FLIP_YZ_ON_LOAD,
    NEGATE_Y_ON_LOAD: CONFIG.NEGATE_Y_ON_LOAD,
    NEGATE_Z_ON_LOAD: CONFIG.NEGATE_Z_ON_LOAD,
    INVERT_X_SIGN: CONFIG.INVERT_X_SIGN,
    INVERT_Y_SIGN: CONFIG.INVERT_Y_SIGN,
    INVERT_Z_SIGN: CONFIG.INVERT_Z_SIGN,
    SHOW_MAPPING_CONTROLS: CONFIG.SHOW_MAPPING_CONTROLS,
    ENFORCE_GLOBAL_MAPPING: CONFIG.ENFORCE_GLOBAL_MAPPING
}));

function lookAtFloor() {
    const cam = document.getElementById('main-camera'); if (cam) cam.setAttribute('rotation', '-90 0 0');
}

console.log('Walkthrough navigation-system.js restored');