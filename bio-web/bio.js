const MAX_SIZE = 5;
const GLC_TO_MAKE_CELLULOSE = 200;
const TIME_TO_LIVE = 60;  // seconds

function Cell(name, createdSimTime) {
    this.name = name;
    this.createdTime = createdSimTime;
    this.storage = {
        glucose: 0,
        atp: 0
    };
    this.sizeX = 1;
    this.sizeY = 1;
    this.cellWall = {
        cellulose: 0
    };
    this.currentDirection = 0;
    this.currentSpeed = 0;
    //this.metabolicRate = 1.0;
    this.chloroplastCount  = 40; // effects photosynthesis output
    this.mitochondriaCount = 20; // effects respiration output
    this.living = true;
    this.lastUpdateTime = 0;
    this.lastRepairCycle = 0;
    this.lastGrowthCycle = 0;
    this.speed = 10;
    this.vx = (Math.random() - 0.5) * this.speed;
    this.vy = (Math.random() - 0.5) * this.speed;
    this.photosynthesis = function(environment) {
        const batch = this.chloroplastCount;
        if (fixGlucoseFromEnvironment(environment, batch)) {
            this.storage.glucose += batch;
        } else {
            console.log('skipping photosynthesis');
        }
    };
    this.respiration = function(environment) {
        const glucoseCost = this.mitochondriaCount;
        if (this.storage.glucose >= glucoseCost &&
            oxidizeGlucoseEquivalent(environment, glucoseCost)) {
            this.storage.glucose -= glucoseCost;
            this.storage.atp += 30 * this.mitochondriaCount;
        } else {
            console.log('skipping respiration');
        }
    };
    this.biosynthesis = function(environment) {
        glucoseCost = GLC_TO_MAKE_CELLULOSE;
        atpCost = 2 * (glucoseCost - 1);
        if (this.storage.atp >= atpCost && this.storage.glucose >= glucoseCost) {
            this.storage.atp -= atpCost;
            this.storage.glucose -= glucoseCost;
            this.cellWall.cellulose += 1;
            this.sizeX = this.cellWall.cellulose;
            this.sizeY = this.cellWall.cellulose;
            return true
        }
        return false
    };
    this.changeDirection = function() {
        atpCost = 500;
        if (this.storage.atp >= atpCost) {
            this.vx = (Math.random() - 0.5) * this.speed;
            this.vy = (Math.random() - 0.5) * this.speed;
            this.storage.atp -= atpCost;
        }
    };
    this.changeSpeed = function(newSpeed) {
        atpCost = 500;
        if (this.storage.atp >= atpCost) {
            this.speed = newSpeed;
            this.storage.atp -= atpCost;
        }
    };
    this.repair = function() {
        atpCost = 20 * 4 * this.cellWall.cellulose;
        if (this.storage.atp >= atpCost) {
            this.storage.atp -= atpCost;
            return true
        }
        return false
    };
    this.homeostasis = function(simTime, environment) {
        // metablism

        // age check (simulation seconds)
        let age = simTime - this.createdTime;
        console.log('age', age, 'storage', this.storage, 'env', environment);

        if (age >= TIME_TO_LIVE || this.cellWall.cellulose > MAX_SIZE) { // programmed suicide
            this.living = false;
            return
        }

        //Low Sugar (Starvation Mode): When sugar levels are low, a sensor called SnRK1 kicks in. It acts like an "emergency brake," slowing down growth and activating pathways to burn stored starch to keep the plant alive.
        //High Sugar (Growth Mode): When photosynthesis is booming and glucose is plentiful, a regulator called TOR (Target of Rapamycin) is activated. TOR is the "green light" for growth—it tells the cell to divide, expand, and use that glucose to build new roots and leaves.
        
        if (this.repair()) {
            this.lastRepairCycle = simTime;
        } else {
            console.log('No repair since', this.lastRepairCycle);
        }
        this.photosynthesis(environment);
        if (this.biosynthesis(environment)) {
            this.changeDirection();
            this.changeSpeed(100);
        } else {
            this.respiration(environment);
        }
    }
    this.update = function(simTime, environment) {
        if (this.living === false) {
            return;
        }

        let deltaTime = simTime - this.lastUpdateTime;
        if (deltaTime >= 1.0) {
            this.homeostasis(simTime, environment);
            this.lastUpdateTime = simTime;
        }
    };
}

function microbialUpdate(simTime, environment, cell) {  // extracellular
    let deltaTime = simTime - cell.lastUpdateTime;

    if (deltaTime >= 5.0) {
        console.log('microbial action!');
    
        console.assert(cell.living === false);
        console.assert(cell.cellWall.cellulose > 0);
        let glucoseCount = 0;

        glucoseCount = cell.storage.glucose;
        if (glucoseCount > 0 && oxidizeGlucoseEquivalent(environment, glucoseCount)) {
            cell.storage.glucose = 0;
        }

        const deltaCellulose = Math.min(0.5, cell.cellWall.cellulose);
        const wallGlucoseEquivalent = deltaCellulose * GLC_TO_MAKE_CELLULOSE;
        if (wallGlucoseEquivalent > 0 &&
            oxidizeGlucoseEquivalent(environment, wallGlucoseEquivalent)) {
            cell.cellWall.cellulose -= deltaCellulose;
            cell.sizeX = cell.cellWall.cellulose;
            cell.sizeY = cell.cellWall.cellulose;
        }
        cell.lastUpdateTime = simTime;
    }
}