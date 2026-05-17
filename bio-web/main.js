const canvas = document.getElementById('simCanvas');
const ctx = canvas.getContext('2d');
const slider = document.getElementById('speedSlider');
const output = document.getElementById('speedValue');
const resetBtn = document.getElementById('resetBtn');
const envCO2El = document.getElementById('envCO2');
const envH2OEl = document.getElementById('envH2O');
const envO2El = document.getElementById('envO2');
const envPanelUpdatedEl = document.getElementById('envPanelUpdated');
const ENV_PANEL_INTERVAL_MS = 1000;

const count = 25;
const baseSpeed = 150.0;
/** Cap simulation dt (seconds) per frame to avoid huge steps after tab backgrounding. */
const MAX_SIM_DELTA = 0.25;

let particles = [];
let cells = [];
let speedMultiplier = 1.0;
let lastFrameTime = 0;
let simTime = 0;
let initialEnvCounts = null;

// Update multiplier immediately when slider moves [21, 28]
slider.addEventListener('input', (e) => {
    speedMultiplier = parseFloat(e.target.value);
    output.textContent = speedMultiplier.toFixed(1);
});

resetBtn.addEventListener('click', init);

function formatCount(n) {
    return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function updateEnvPanel() {
    envCO2El.textContent = formatCount(universe.CO2Count);
    envH2OEl.textContent = formatCount(universe.H2OCount);
    envO2El.textContent = formatCount(universe.O2Count);
    envPanelUpdatedEl.textContent =
        'Updated ' + new Date().toLocaleTimeString();
}

setInterval(updateEnvPanel, ENV_PANEL_INTERVAL_MS);

function snapshotEnvCounts(env) {
    return { CO2: env.CO2Count, H2O: env.H2OCount, O2: env.O2Count };
}

function hasOrganicMatter() {
    return particles.some((p) =>
        p instanceof Cell &&
        (p.living || p.storage.glucose > 0 || p.cellWall.cellulose > 0)
    );
}

function checkEnvConservation() {
    if (!initialEnvCounts || hasOrganicMatter()) {
        return;
    }
    const cur = snapshotEnvCounts(universe);
    const drift = {
        CO2: cur.CO2 - initialEnvCounts.CO2,
        H2O: cur.H2O - initialEnvCounts.H2O,
        O2: cur.O2 - initialEnvCounts.O2,
    };
    if (Math.abs(drift.CO2) > 0 ||
        Math.abs(drift.H2O) > 0 ||
        Math.abs(drift.O2) > 0) {
        console.warn('Environment conservation drift after teardown', drift, {
            initial: initialEnvCounts,
            current: cur,
        });
    }
}

// Initialize particles with floating-point positions and velocities
function init() {
    simTime = 0;
    lastFrameTime = 0;
    particles = []; // Clear existing state
    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * baseSpeed,
            vy: (Math.random() - 0.5) * baseSpeed
        });
    }
    //cells = [];
    for (let i = 0; i < 100; i++) {
        let luca = new Cell("Luca", simTime);
        luca.x = Math.random() * canvas.width;
        luca.y = Math.random() * canvas.height;
        particles.push(luca);
        luca = null;
    }
    //cells.push(luca);
    initialEnvCounts = snapshotEnvCounts(universe);
    updateEnvPanel();
}

function draw(currentTime) {
    let wallDeltaSec = 0;
    if (lastFrameTime === 0) {
        lastFrameTime = currentTime;
    } else {
        wallDeltaSec = (currentTime - lastFrameTime) / 1000;
        lastFrameTime = currentTime;
    }
    const simDelta = Math.min(wallDeltaSec * speedMultiplier, MAX_SIM_DELTA);
    simTime += simDelta;

     // 1. Clear the raster surface
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#0f0';

    let cleanupList = [];

    particles.forEach((p, index) => {
        p.x += p.vx * simDelta;
        p.y += p.vy * simDelta;

        // 3. Handle Wrap-Around logic
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        // 4. Rasterize: Render as a 2x2 pixel block
        // Browser handles float-to-pixel snapping automatically
        if (p instanceof Cell) {
            if (p.living) {
                ctx.fillStyle = '#0ff';
                p.update(simTime, universe);
            } else {
                ctx.fillStyle = '#f00';
                if (p.cellWall.cellulose > 0) {
                    microbialUpdate(simTime, universe, p);
                } else {
                    cleanupList.push(index);
                }
            }
            ctx.fillRect(p.x, p.y, p.sizeX, p.sizeY);
        } else {
            ctx.fillStyle = '#0f0';
            ctx.fillRect(p.x, p.y, 2, 2);
        }
    });

    // perform cleanup
    for (const index of cleanupList) {
        particles.splice(index, 1);
    }
    checkEnvConservation();

    requestAnimationFrame(draw);
  }

  // Initial setup and start loop
  init();
  requestAnimationFrame(draw);