/* navigation-system-swap_yz.js - FLIP Y/Z on load (same as default) */

/* eslint-disable */
const CONFIG = {
    DATA_FILE: 'cone_data.json',
    PANORAMA_BASE_PATH: 'panoramas/',
    SPHERE_SIZE_DEFAULT: 0.0875,
    FLIP_YZ_ON_LOAD: true,
    NEGATE_Y_ON_LOAD: false,
    NEGATE_Z_ON_LOAD: false
};

// Rest of code is identical to original navigation-system.js implementation
// (keeps behavior consistent but exposes explicit flags for clarity)

/* Utility and core functions copied from original navigation-system.js */
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

let state = { cones: [], currentCone: null };
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
    if (state.cones && state.cones.length > 0) {
        const p0 = state.cones[0].dxf_position || state.cones[0].position || {};
        console.log('First cone original dxf_position:', JSON.stringify(p0));
    }
    if (CONFIG.FLIP_YZ_ON_LOAD) {
        state.cones.forEach((cone) => {
            const p = cone.dxf_position || cone.position;
            if (p && typeof p.y === 'number' && typeof p.z === 'number') {
                const tmp = p.y; p.y = p.z; p.z = tmp;
            }
        });
    }
    // Apply negation flags if requested
    if (CONFIG.NEGATE_Y_ON_LOAD || CONFIG.NEGATE_Z_ON_LOAD) {
        state.cones.forEach((cone) => {
            const p = cone.dxf_position || cone.position;
            if (!p) return;
            if (CONFIG.NEGATE_Y_ON_LOAD && typeof p.y === 'number') p.y = -p.y;
            if (CONFIG.NEGATE_Z_ON_LOAD && typeof p.z === 'number') p.z = -p.z;
            // Also invert direction vectors
            if (cone.direction) {
                if (cone.direction.forward) {
                    if (CONFIG.NEGATE_Y_ON_LOAD && typeof cone.direction.forward.y === 'number') cone.direction.forward.y = -cone.direction.forward.y;
                    if (CONFIG.NEGATE_Z_ON_LOAD && typeof cone.direction.forward.z === 'number') cone.direction.forward.z = -cone.direction.forward.z;
                }
                if (cone.direction.up) {
                    if (CONFIG.NEGATE_Y_ON_LOAD && typeof cone.direction.up.y === 'number') cone.direction.up.y = -cone.direction.up.y;
                    if (CONFIG.NEGATE_Z_ON_LOAD && typeof cone.direction.up.z === 'number') cone.direction.up.z = -cone.direction.up.z;
                }
            }
        });
    }
    if (state.cones && state.cones.length > 0) {
        const p0b = state.cones[0].dxf_position || state.cones[0].position || {};
        console.log('First cone dxf_position after processing:', JSON.stringify(p0b));
    }
    const totalEl = document.getElementById('total-cones'); if (totalEl) totalEl.textContent = (state.cones.length || 0);
    return data;
}

// Minimal remaining functions needed by the page: createSphereForCone, populateScene,
// navigateToCone, loadPanorama, applySkyRotation, wireUI, init.
// For brevity reuse the implementations from the original script by loading the original
// navigation-system.js logic - since we can't import here, we'll keep a minimal wiring
// that delegates the heavy lifting to the loaded A-Frame scene.

function createSphereForCone(cone, idx) {
    const container = document.getElementById('spheres-container');
    const sphere = document.createElement('a-sphere');
    sphere.setAttribute('class', 'clickable nav-sphere');
    sphere.setAttribute('radius', CONFIG.SPHERE_SIZE_DEFAULT);
    const p = cone.dxf_position || cone.position || cone;
    const pos = `${p.x} ${p.z} ${-p.y}`;
    sphere.setAttribute('position', pos);
    sphere.addEventListener('click', () => navigateToCone(cone));
    container.appendChild(sphere);
    cone._sphere = sphere;
}

async function populateScene() { const container = document.getElementById('spheres-container'); container.innerHTML = ''; state.cones.forEach((c, i) => createSphereForCone(c, i)); }

function setCurrentConeUI(cone) { const el = document.getElementById('current-cone-id'); if (el) el.textContent = cone.cone_id || cone.id || ''; }

async function navigateToCone(cone) { if (!cone) return; state.currentCone = cone; setCurrentConeUI(cone); const rig = document.getElementById('camera-rig'); const p = cone.dxf_position || cone.position || cone; if (rig) rig.setAttribute('position', `${p.x} ${p.z} ${-p.y}`); try { await loadPanorama(cone.image_path || cone.filename || cone.image || ''); if (cone.direction) applySkyRotation(cone.direction); } catch (e) { console.warn('Failed to load panorama for cone', e); } }

function loadPanorama(imagePath) { return new Promise((resolve, reject) => { const sky = document.getElementById('panorama-sky'); const imgPathNorm = (imagePath || '').replace(/^\.\//, '').replace(/^\//, ''); const full = imgPathNorm.startsWith(CONFIG.PANORAMA_BASE_PATH) ? imgPathNorm : (CONFIG.PANORAMA_BASE_PATH + imgPathNorm); const img = new Image(); img.crossOrigin = 'anonymous'; img.onload = () => { if (sky) sky.setAttribute('src', full); const cam = document.getElementById('main-camera'); if (cam) cam.setAttribute('rotation', '0 0 0'); resolve(full); }; img.onerror = () => reject(new Error('Failed to load ' + full)); img.src = full; }); }

function applySkyRotation(direction) {
    const sky = document.getElementById('panorama-sky'); if (!sky || !direction) return; let yaw = 0, pitch = 0, roll = 0; if (direction.forward && direction.up) {
        const forward = new THREE.Vector3(direction.forward.x, direction.forward.z, -direction.forward.y).normalize();
        const up = new THREE.Vector3(-direction.up.x, -direction.up.z, direction.up.y).normalize();
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
    const snappedYaw = Math.round(yaw / 90) * 90;
    const totalYaw = (snappedYaw + (state.skyYawOffset || 0)) % 360;
    sky.setAttribute('rotation', { x: 0, y: totalYaw, z: 0 });
}

function wireUI() { const toggle = document.getElementById('sphere-toggle'); if (toggle) toggle.addEventListener('change', () => document.getElementById('spheres-container').style.display = toggle.checked ? '' : 'none'); const size = document.getElementById('sphere-size'); if (size) size.addEventListener('input', () => document.querySelectorAll('.nav-sphere').forEach(s => s.setAttribute('radius', size.value))); const elevation = document.getElementById('sphere-elevation'); if (elevation) elevation.addEventListener('input', () => document.querySelectorAll('.nav-sphere').forEach((s, i) => { const c = state.cones[i]; if (!c) return; const p = c.dxf_position || c.position || c; s.setAttribute('position', `${p.x} ${p.z + parseFloat(elevation.value)} ${-p.y}`); })); const exportBtn = document.getElementById('export-data'); if (exportBtn) exportBtn.addEventListener('click', () => { if (!state.cones || state.cones.length === 0) return alert('No data to export'); const blob = new Blob([JSON.stringify({ cones: state.cones }, null, 2)], { type: 'application/json' }); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'cone_data_export.json'; a.click(); URL.revokeObjectURL(a.href); }); const reset = document.getElementById('reset-view'); if (reset) reset.addEventListener('click', () => { const rig = document.getElementById('camera-rig'); if (rig) rig.setAttribute('position', '0 1.6 0'); const cam = document.getElementById('main-camera'); if (cam) cam.setAttribute('rotation', '0 0 0'); }); const rotateBtn = document.getElementById('rotate-sky'); if (rotateBtn) rotateBtn.addEventListener('click', () => rotateSkyBy(90)); const rotateXBtn = document.getElementById('rotate-sky-x'); if (rotateXBtn) rotateXBtn.addEventListener('click', () => rotateSkyAxis('x', 90)); const rotateZBtn = document.getElementById('rotate-sky-z'); if (rotateZBtn) rotateZBtn.addEventListener('click', () => rotateSkyAxis('z', 90)); const resetSkyBtn = document.getElementById('reset-sky'); if (resetSkyBtn) resetSkyBtn.addEventListener('click', () => { state.skyYawOffset = 0; const sky = document.getElementById('panorama-sky'); if (sky) sky.setAttribute('rotation', { x: 0, y: 0, z: 0 }); }); window.addEventListener('keydown', (ev) => { if (ev.key === 'r' || ev.key === 'R') rotateSkyBy(90); if (ev.key === 'x' || ev.key === 'X') rotateSkyAxis('x', 90); if (ev.key === 'z' || ev.key === 'Z') rotateSkyAxis('z', 90); }); }

async function init() { try { await loadConeData(); await populateScene(); wireUI(); if (state.cones && state.cones.length > 0) navigateToCone(state.cones[0]); } catch (e) { console.error('Navigation init failed', e); } }

document.addEventListener('DOMContentLoaded', init);

function rotateSkyBy(deg) { const sky = document.getElementById('panorama-sky'); if (!sky) return; let rot = sky.getAttribute('rotation'); if (!rot) rot = { x: 0, y: 0, z: 0 }; let y = 0; if (typeof rot === 'string') { const parts = rot.split(' ').map(Number); y = parts.length >= 2 ? parts[1] : 0; } else { y = rot.y || 0; } state.skyYawOffset = ((state.skyYawOffset || 0) + deg) % 360; const newY = (y + deg) % 360; sky.setAttribute('rotation', { x: 0, y: newY, z: 0 }); }

function rotateSkyAxis(axis, deg) { const sky = document.getElementById('panorama-sky'); if (!sky) return; let rot = sky.getAttribute('rotation') || { x: 0, y: 0, z: 0 }; let cx = 0, cy = 0, cz = 0; if (typeof rot === 'string') { const parts = rot.split(' ').map(Number); cx = parts[0] || 0; cy = parts[1] || 0; cz = parts[2] || 0; } else { cx = rot.x || 0; cy = rot.y || 0; cz = rot.z || 0; } let nx = cx, ny = cy, nz = cz; switch ((axis || 'y').toLowerCase()) { case 'x': nx = (cx + deg) % 360; break; case 'y': ny = (cy + deg) % 360; break; case 'z': nz = (cz + deg) % 360; break; } if ((axis || 'y').toLowerCase() === 'y') { rotateSkyBy(deg); return; } sky.setAttribute('rotation', { x: nx, y: ny, z: nz }); }

console.log('navigation-system-swap_yz.js loaded');
