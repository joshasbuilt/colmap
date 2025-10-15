/**
 * 360° Cone-Based Navigation System
 * Advanced A-Frame navigation with metallic materials and professional lighting
 * 
 * COORDINATE SYSTEM CONVERSION:
 * DXF uses Z-up coordinate system (X, Y, Z where Z is vertical)
 * A-Frame uses Y-up coordinate system (X, Y, Z where Y is vertical)
 * Conversion: DXF(x,y,z) -> A-Frame(x, z, -y)
 *   - X stays X (left/right)
 *   - DXF Y becomes A-Frame -Z (depth/forward-back, negated to fix mirroring)
 *   - DXF Z becomes A-Frame Y (height/up-down)
 */

// Global State Management
const state = {
    cones: [],
    currentCone: null,
    sphereElevation: -0.7,
    sphereSize: 0.0875,
    pathRibbons: [],
    commentMarkers: [],
    currentSkyObjectUrl: null,
    scene: null,
    camera: null,
    envMap: null,
    sharedMaterial: null,
    manualPitch: 0,
    manualRoll: 0,
    mouseControlEnabled: false
};

// Configuration
const CONFIG = {
    DATA_FILE: 'cone_data.json',
    PANORAMA_BASE_PATH: '',
    SPHERE_SEGMENTS: 32,
    RIBBON_WIDTH: 0.03,
    COMMENT_SIZE: 0.15,
    MOUSE_SENSITIVITY: 1.0,
    PITCH_OFFSET: 0,  // Global pitch correction (degrees, positive = look up, negative = look down)
    ROLL_OFFSET: 0    // Global roll correction (degrees)
};

/**
 * Initialize the navigation system
 */
async function init() {
    console.log('Initializing 360° Navigation System...');
    
    // Wait for A-Frame scene to load
    const scene = document.querySelector('a-scene');
    
    if (scene.hasLoaded) {
        await onSceneReady();
    } else {
        scene.addEventListener('loaded', onSceneReady);
    }
}

/**
 * Scene ready callback
 */
async function onSceneReady() {
    state.scene = document.querySelector('a-scene');
    state.camera = document.querySelector('#main-camera');
    
    console.log('Scene loaded, fetching cone data...');
    
    // Load cone data
    try {
        await loadConeData();
        initializeUI();
        console.log(`Loaded ${state.cones.length} cones successfully`);
        
        // Start with first cone if available
        if (state.cones.length > 0) {
            // Position camera at first cone location
            const firstCone = state.cones[0];
            const cameraRig = document.getElementById('camera-rig');
            
            // Convert DXF to A-Frame coordinates
            const position = {
                x: firstCone.dxf_position.x,
                y: firstCone.dxf_position.z,  // DXF Z -> A-Frame Y (height)
                z: -firstCone.dxf_position.y  // DXF Y -> A-Frame -Z (negated)
            };
            
            cameraRig.setAttribute('position', position);
            
            // Load first panorama and apply sky rotation
            navigateToCone(firstCone);
        }
    } catch (error) {
        console.error('Failed to initialize navigation system:', error);
        alert('Failed to load navigation data. Please check the console for details.');
    }
}

/**
 * Load cone data from JSON file
 */
async function loadConeData() {
    try {
        const response = await fetch(CONFIG.DATA_FILE);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        state.cones = data.cones;
        
        // Update UI info
        document.getElementById('total-cones').textContent = data.export_info.total_cones;
        document.getElementById('camera-index').textContent = data.export_info.camera_index_used;
        
        // Create shared metallic material
        createSharedMaterial();
        
        // Generate navigation spheres and path connections
        generateNavigationSpheres();
        generatePathRibbons();
        
    } catch (error) {
        console.error('Error loading cone data:', error);
        throw error;
    }
}

/**
 * Create shared metallic material for spheres and ribbons
 */
function createSharedMaterial() {
    const scene = state.scene.object3D;
    
    // Create PMREM environment map generator
    const pmremGenerator = new THREE.PMREMGenerator(state.scene.renderer);
    pmremGenerator.compileEquirectangularShader();
    
    // Create metallic physical material
    state.sharedMaterial = new THREE.MeshPhysicalMaterial({
        color: 0xeeeeee,
        metalness: 0.6,
        roughness: 0.12,
        clearcoat: 0.2,
        clearcoatRoughness: 0.08,
        envMapIntensity: 0.9,
        reflectivity: 0.85,
        transparent: true,
        opacity: 0.9,
        side: THREE.DoubleSide
    });
    
    console.log('Created shared metallic material');
}

/**
 * Update environment map from current sky texture
 */
function updateEnvironmentMap(skyTexture) {
    if (!skyTexture || !state.sharedMaterial) return;
    
    try {
        const pmremGenerator = new THREE.PMREMGenerator(state.scene.renderer);
        const envMap = pmremGenerator.fromEquirectangular(skyTexture).texture;
        
        state.sharedMaterial.envMap = envMap;
        state.sharedMaterial.needsUpdate = true;
        
        pmremGenerator.dispose();
        
        console.log('Updated environment map for metallic reflections');
    } catch (error) {
        console.error('Error updating environment map:', error);
    }
}

/**
 * Generate navigation spheres for all cones
 */
function generateNavigationSpheres() {
    const container = document.getElementById('spheres-container');
    
    state.cones.forEach((cone, index) => {
        const sphere = createNavigationSphere(cone, index);
        container.appendChild(sphere);
    });
    
    console.log(`Generated ${state.cones.length} navigation spheres`);
}

/**
 * Create a single navigation sphere
 */
function createNavigationSphere(cone, index) {
    const sphere = document.createElement('a-sphere');
    
    // Calculate position with elevation offset
    // Convert DXF (Z-up) to A-Frame (Y-up): swap Y and Z, negate Z to fix mirroring
    const position = {
        x: cone.dxf_position.x,
        y: cone.dxf_position.z + state.sphereElevation,  // DXF Z becomes A-Frame Y (height)
        z: -cone.dxf_position.y  // DXF Y becomes A-Frame -Z (depth, negated to fix mirror)
    };
    
    // Set sphere attributes
    sphere.setAttribute('radius', state.sphereSize);
    sphere.setAttribute('position', position);
    sphere.setAttribute('segments-width', CONFIG.SPHERE_SEGMENTS);
    sphere.setAttribute('segments-height', CONFIG.SPHERE_SEGMENTS);
    sphere.setAttribute('class', 'clickable navigation-sphere');
    sphere.setAttribute('data-cone-index', index);
    
    // Apply metallic material using A-Frame material component
    sphere.setAttribute('material', {
        shader: 'standard',
        color: '#ffffff',
        metalness: 0.5,
        roughness: 0.2,
        opacity: 0.9,
        transparent: true
    });
    
    // Add click event listener
    sphere.addEventListener('click', function() {
        navigateToCone(cone);
    });
    
    // Add hover effects
    sphere.addEventListener('mouseenter', function() {
        sphere.setAttribute('scale', '1.2 1.2 1.2');
        sphere.setAttribute('material', 'opacity', 1.0);
    });
    
    sphere.addEventListener('mouseleave', function() {
        sphere.setAttribute('scale', '1 1 1');
        sphere.setAttribute('material', 'opacity', 0.9);
    });
    
    // Store reference
    cone.sphereElement = sphere;
    
    return sphere;
}

/**
 * Generate path ribbons connecting consecutive spheres
 */
function generatePathRibbons() {
    const container = document.getElementById('ribbons-container');
    
    // Clear existing ribbons
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }
    state.pathRibbons = [];
    
    // Create ribbons between consecutive cones
    for (let i = 0; i < state.cones.length - 1; i++) {
        const startCone = state.cones[i];
        const endCone = state.cones[i + 1];
        
        const ribbon = createPathRibbon(startCone, endCone);
        container.appendChild(ribbon);
        state.pathRibbons.push(ribbon);
    }
    
    console.log(`Generated ${state.pathRibbons.length} path ribbons`);
}

/**
 * Create a path ribbon between two cones
 */
function createPathRibbon(startCone, endCone) {
    const entity = document.createElement('a-entity');
    
    // Get positions from the actual sphere elements (which include perspective correction)
    const startPos = startCone.sphereElement ? startCone.sphereElement.getAttribute('position') : null;
    const endPos = endCone.sphereElement ? endCone.sphereElement.getAttribute('position') : null;
    
    if (!startPos || !endPos) return entity;
    
    const start = new THREE.Vector3(startPos.x, startPos.y, startPos.z);
    const end = new THREE.Vector3(endPos.x, endPos.y, endPos.z);
    
    // Calculate midpoint and direction
    const midpoint = new THREE.Vector3().lerpVectors(start, end, 0.5);
    const direction = new THREE.Vector3().subVectors(end, start);
    const distance = direction.length();
    
    // Create ribbon geometry
    const geometry = new THREE.PlaneGeometry(distance, CONFIG.RIBBON_WIDTH);
    
    // Apply shared metallic material
    const mesh = new THREE.Mesh(geometry, state.sharedMaterial.clone());
    mesh.material.opacity = 0.7;
    
    // Position and rotate mesh
    mesh.position.copy(midpoint);
    mesh.lookAt(end);
    mesh.rotateY(Math.PI / 2);
    
    // Add mesh to entity
    entity.setObject3D('mesh', mesh);
    
    return entity;
}

/**
 * Navigate to a specific cone
 */
async function navigateToCone(cone) {
    if (!cone) return;
    
    console.log(`Navigating to cone ${cone.cone_id}...`);
    
    // Show loading indicator
    showLoading(true);
    
    try {
        // Update current cone
        state.currentCone = cone;
        document.getElementById('current-cone-id').textContent = cone.cone_id;
        
        // Move camera to cone position
        const cameraRig = document.getElementById('camera-rig');
        const position = {
            x: cone.dxf_position.x,
            y: cone.dxf_position.z,  // DXF Z -> A-Frame Y (height)
            z: -cone.dxf_position.y  // DXF Y -> A-Frame -Z (negated)
        };
        cameraRig.setAttribute('position', position);
        
        // Update sphere positions based on new camera location (perspective correction)
        updateSphereElevation();
        
        // Load and apply panorama
        await loadPanorama(cone.image_path);
        
        // Apply sky rotation based on direction vector
        applySkyRotation(cone.direction);
        
        // Highlight current sphere
        highlightCurrentSphere(cone);
        
    } catch (error) {
        console.error('Error navigating to cone:', error);
        alert('Failed to load panorama. Please check the image path.');
    } finally {
        showLoading(false);
    }
}

/**
 * Load panorama image
 */
async function loadPanorama(imagePath) {
    return new Promise((resolve, reject) => {
        const sky = document.getElementById('panorama-sky');
        const fullPath = CONFIG.PANORAMA_BASE_PATH + imagePath;
        
        console.log(`Loading panorama: ${fullPath}`);
        
        // Create a new image to preload
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        img.onload = () => {
            // Revoke old object URL if exists
            if (state.currentSkyObjectUrl) {
                URL.revokeObjectURL(state.currentSkyObjectUrl);
            }
            
            // Set sky source
            sky.setAttribute('src', fullPath);
            
            // Update environment map for metallic reflections
            setTimeout(() => {
                const texture = sky.components.material.material.map;
                if (texture) {
                    updateEnvironmentMap(texture);
                }
            }, 100);
            
            resolve();
        };
        
        img.onerror = () => {
            reject(new Error(`Failed to load image: ${fullPath}`));
        };
        
        img.src = fullPath;
    });
}

/**
 * Apply sky rotation based on direction vectors (forward and up)
 */
function applySkyRotation(direction) {
    if (!direction) return;
    
    const sky = document.getElementById('panorama-sky');
    if (!sky) return;
    
    // Check if we have the new format with forward and up vectors
    const hasFullOrientation = direction.forward && direction.up;
    
    let pitch, yaw, roll;
    
    if (hasFullOrientation) {
        // Convert DXF forward and up vectors to A-Frame coordinates
        // DXF(x,y,z) -> A-Frame(x, z, -y)
        // For skybox: invert the up vector to fix upside-down issue
        const forward = new THREE.Vector3(
            direction.forward.x,
            direction.forward.z,
            -direction.forward.y
        );
        forward.normalize();
        
        const up = new THREE.Vector3(
            -direction.up.x,    // Invert X
            -direction.up.z,    // Invert Y (was Z in DXF)
            direction.up.y      // Invert Z (was -Y in DXF)
        );
        up.normalize();
        
        // Build orthonormal basis from forward and up vectors
        // In THREE.js/A-Frame: X=right, Y=up, Z=back (camera looks down -Z)
        const right = new THREE.Vector3().crossVectors(up, forward);
        right.normalize();
        
        // Recompute up to ensure orthogonality
        const correctedUp = new THREE.Vector3().crossVectors(forward, right);
        correctedUp.normalize();
        
        // Build rotation matrix: columns are [right, up, -forward] since camera looks down -Z
        const rotMatrix = new THREE.Matrix4();
        rotMatrix.set(
            right.x, correctedUp.x, -forward.x, 0,
            right.y, correctedUp.y, -forward.y, 0,
            right.z, correctedUp.z, -forward.z, 0,
            0, 0, 0, 1
        );
        
        // Extract Euler angles (XYZ order) from rotation matrix
        const euler = new THREE.Euler().setFromRotationMatrix(rotMatrix, 'YXZ');
        
        // Convert to degrees
        pitch = euler.x * (180 / Math.PI) + CONFIG.PITCH_OFFSET;     // Add global pitch offset
        yaw = euler.y * (180 / Math.PI) + 90;  // Add 90° to fix left rotation
        roll = -(euler.z * (180 / Math.PI)) + CONFIG.ROLL_OFFSET;   // Negate roll and add offset
        
        console.log(`%c[SKYBOX ROTATION] yaw=${yaw.toFixed(2)}°, pitch=${pitch.toFixed(2)}° (raw: ${(euler.x * (180 / Math.PI)).toFixed(2)}°), roll=${roll.toFixed(2)}°`, 'background: #222; color: #bada55; font-weight: bold; padding: 2px 5px;');
        
    } else {
        // Old format: single direction vector
        // Convert DXF direction vector to A-Frame coordinates
        const dirVec = new THREE.Vector3(
            direction.x,
            direction.z,
            -direction.y
        );
        dirVec.normalize();
        
        // Calculate yaw only (pitch and roll approximations don't work well)
        yaw = Math.atan2(dirVec.x, dirVec.z) * (180 / Math.PI);
        pitch = -Math.asin(Math.max(-1, Math.min(1, dirVec.y))) * (180 / Math.PI) * -2.0;
        roll = Math.atan2(dirVec.x, dirVec.z) * dirVec.y * (180 / Math.PI);
        
        console.log(`Single direction - yaw=${yaw.toFixed(2)}°, pitch=${pitch.toFixed(2)}°, roll=${roll.toFixed(2)}°`);
    }
    
    // Apply rotation to sky with all three axes
    // A-Frame rotation: X=pitch (up/down), Y=yaw (left/right), Z=roll (tilt)
    const finalPitch = state.mouseControlEnabled ? state.manualPitch : pitch;
    const finalRoll = state.mouseControlEnabled ? state.manualRoll : roll;
    
    sky.setAttribute('rotation', {
        x: finalPitch,     // Pitch (up/down) on X axis
        y: yaw,            // Yaw (left/right rotation)
        z: finalRoll       // Roll (tilt) on Z axis
    });
    
    console.log(`Applied sky rotation: yaw=${yaw.toFixed(2)}°, pitch=${finalPitch.toFixed(2)}°, roll=${finalRoll.toFixed(2)}° (manual control: ${state.mouseControlEnabled})`);
}

/**
 * Highlight the current sphere
 */
function highlightCurrentSphere(cone) {
    // Reset all spheres
    state.cones.forEach(c => {
        if (c.sphereElement) {
            c.sphereElement.setAttribute('material', 'color', '#ffffff');
        }
    });
    
    // Highlight current
    if (cone.sphereElement) {
        cone.sphereElement.setAttribute('material', 'color', '#667eea');
    }
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    const indicator = document.getElementById('loading-indicator');
    if (show) {
        indicator.classList.remove('hidden');
    } else {
        indicator.classList.add('hidden');
    }
}

/**
 * Initialize UI controls
 */
function initializeUI() {
    // Panel toggle
    const togglePanelBtn = document.getElementById('toggle-panel');
    const panel = document.getElementById('ui-panel');
    
    // Collapse panel by default on launch
    panel.classList.add('minimized');
    togglePanelBtn.textContent = '+';
    
    togglePanelBtn.addEventListener('click', () => {
        panel.classList.toggle('minimized');
        togglePanelBtn.textContent = panel.classList.contains('minimized') ? '+' : '−';
    });
    
    // Sphere toggle
    const sphereToggle = document.getElementById('sphere-toggle');
    sphereToggle.addEventListener('change', (e) => {
        const container = document.getElementById('spheres-container');
        container.setAttribute('visible', e.target.checked);
    });
    
    // Sphere size control
    const sphereSize = document.getElementById('sphere-size');
    const sphereSizeValue = document.getElementById('sphere-size-value');
    
    sphereSize.addEventListener('input', (e) => {
        state.sphereSize = parseFloat(e.target.value);
        sphereSizeValue.textContent = state.sphereSize.toFixed(4);
        updateSphereSize();
    });
    
    // Elevation control
    const elevation = document.getElementById('sphere-elevation');
    const elevationValue = document.getElementById('elevation-value');
    
    // Set initial elevation value
    elevation.value = state.sphereElevation;
    elevationValue.textContent = state.sphereElevation.toFixed(1);
    
    elevation.addEventListener('input', (e) => {
        state.sphereElevation = parseFloat(e.target.value);
        elevationValue.textContent = state.sphereElevation.toFixed(1);
        updateSphereElevation();
    });
    
    // Comment controls
    document.getElementById('toggle-comments').addEventListener('click', toggleComments);
    document.getElementById('add-comment').addEventListener('click', addComment);
    
    // Export data
    document.getElementById('export-data').addEventListener('click', exportData);
    
    // Reset view
    document.getElementById('reset-view').addEventListener('click', resetView);
    
    // Add mouse controls for manual pitch/roll adjustment
    document.addEventListener('keydown', (e) => {
        const sky = document.getElementById('panorama-sky');
        if (!sky) return;
        
        const step = 1; // 1 degree per key press
        
        switch(e.key.toLowerCase()) {
            case 'q': // Roll left
                state.manualRoll -= step;
                break;
            case 'e': // Roll right
                state.manualRoll += step;
                break;
            case 'w': // Pitch up
                state.manualPitch += step;
                break;
            case 's': // Pitch down
                state.manualPitch -= step;
                break;
            case 'r': // Reset manual adjustments
                state.manualPitch = 0;
                state.manualRoll = 0;
                break;
            default:
                return;
        }
        
        // Apply the manual rotation
        const currentYaw = parseFloat(sky.getAttribute('rotation').y) || 0;
        sky.setAttribute('rotation', {
            x: state.manualPitch,  // Pitch on X axis
            y: currentYaw,
            z: state.manualRoll    // Roll on Z axis
        });
        
        console.log(`MANUAL ADJUSTMENT: pitch=${state.manualPitch.toFixed(2)}°, roll=${state.manualRoll.toFixed(2)}° (Q/E=roll, W/S=pitch, R=reset)`);
    });
    
    console.log('Manual controls enabled: Q/E for roll, W/S for pitch, R to reset');
}

/**
 * Update sphere size for all navigation spheres
 */
function updateSphereSize() {
    state.cones.forEach(cone => {
        if (cone.sphereElement) {
            cone.sphereElement.setAttribute('radius', state.sphereSize);
        }
    });
}

/**
 * Update sphere elevation for all navigation spheres and ribbons
 */
function updateSphereElevation() {
    const cameraRig = document.getElementById('camera-rig');
    const camPos = cameraRig ? cameraRig.getAttribute('position') : { x: 0, y: 1.6, z: 0 };
    
    state.cones.forEach(cone => {
        if (cone.sphereElement) {
            // Convert DXF (Z-up) to A-Frame (Y-up): swap Y and Z, negate Z to fix mirroring
            const baseX = cone.dxf_position.x;
            const baseY = cone.dxf_position.z + state.sphereElevation;  // DXF Z -> A-Frame Y
            const baseZ = -cone.dxf_position.y;  // DXF Y -> A-Frame -Z (negated)
            
            // Calculate horizontal distance from camera
            const dx = baseX - camPos.x;
            const dz = baseZ - camPos.z;
            const distance = Math.sqrt(dx * dx + dz * dz);
            
            // Apply perspective correction: lower distant spheres
            // The factor 0.002016 can be adjusted - higher = more correction
            const perspectiveCorrection = (distance * distance) * 0.002016;
            
            cone.sphereElement.setAttribute('position', {
                x: baseX,
                y: baseY - perspectiveCorrection,
                z: baseZ
            });
        }
    });
    
    // Regenerate ribbons with new elevation
    generatePathRibbons();
}

/**
 * Toggle comment markers visibility
 */
function toggleComments() {
    const container = document.getElementById('comments-container');
    const currentVisibility = container.getAttribute('visible');
    container.setAttribute('visible', currentVisibility === 'false');
}

/**
 * Add a comment marker at the current cone position
 */
function addComment() {
    if (!state.currentCone) {
        alert('Please navigate to a cone first');
        return;
    }
    
    const container = document.getElementById('comments-container');
    const comment = createCommentMarker(state.currentCone);
    container.appendChild(comment);
    state.commentMarkers.push(comment);
    
    console.log(`Added comment at cone ${state.currentCone.cone_id}`);
}

/**
 * Create a comment/annotation marker
 */
function createCommentMarker(cone) {
    const entity = document.createElement('a-entity');
    
    // Position above the cone
    // Convert DXF (Z-up) to A-Frame (Y-up): swap Y and Z, negate Z to fix mirroring
    const position = {
        x: cone.dxf_position.x,
        y: cone.dxf_position.z + state.sphereElevation + 0.3,  // DXF Z -> A-Frame Y
        z: -cone.dxf_position.y  // DXF Y -> A-Frame -Z (negated)
    };
    
    // Create tablet-like box with grid pattern
    const box = document.createElement('a-box');
    box.setAttribute('width', CONFIG.COMMENT_SIZE);
    box.setAttribute('height', CONFIG.COMMENT_SIZE * 0.7);
    box.setAttribute('depth', 0.01);
    box.setAttribute('position', position);
    box.setAttribute('class', 'clickable comment-marker');
    
    // Metallic material
    box.setAttribute('material', {
        shader: 'standard',
        color: '#e0e0e0',
        metalness: 0.7,
        roughness: 0.15
    });
    
    // Add click interaction
    box.addEventListener('click', () => {
        alert(`Comment Marker\nCone ID: ${cone.cone_id}\nPosition: ${JSON.stringify(cone.dxf_position, null, 2)}`);
    });
    
    // Add hover effect
    box.addEventListener('mouseenter', () => {
        box.setAttribute('material', 'color', '#ffffff');
    });
    
    box.addEventListener('mouseleave', () => {
        box.setAttribute('material', 'color', '#e0e0e0');
    });
    
    entity.appendChild(box);
    
    // Generate unique ID
    entity.setAttribute('id', `comment-${Date.now()}`);
    
    return entity;
}

/**
 * Export current state data
 */
function exportData() {
    const exportData = {
        timestamp: new Date().toISOString(),
        current_cone: state.currentCone ? state.currentCone.cone_id : null,
        sphere_settings: {
            elevation: state.sphereElevation,
            size: state.sphereSize
        },
        comment_markers: state.commentMarkers.map(marker => ({
            id: marker.getAttribute('id'),
            position: marker.firstChild.getAttribute('position')
        }))
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `navigation-state-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
    
    console.log('Exported navigation state');
}

/**
 * Reset view to initial state
 */
function resetView() {
    if (state.cones.length > 0) {
        navigateToCone(state.cones[0]);
    }
    
    state.camera.setAttribute('rotation', '0 0 0');
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', init);

// Error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

console.log('Navigation system script loaded');

