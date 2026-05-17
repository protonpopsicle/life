// Simplified photosynthesis / respiration stoichiometry (per glucose equivalent).
// Fixation:  6 CO2 + 6 H2O -> C6H12O6 + 6 O2
// Oxidation: C6H12O6 + 6 O2 -> 6 CO2 + 6 H2O

const STOICH = Object.freeze({
    CO2_PER_GLC: 6,
    H2O_PER_GLC: 6,
    O2_PER_GLC: 6,
});

function fixationCost(n) {
    return {
        co2: STOICH.CO2_PER_GLC * n,
        h2o: STOICH.H2O_PER_GLC * n,
        o2: STOICH.O2_PER_GLC * n,
    };
}

function canFixGlucoseFromEnvironment(environment, n) {
    if (n <= 0 || environment.light <= 0) {
        return false;
    }
    const cost = fixationCost(n);
    return environment.CO2Count >= cost.co2 && environment.H2OCount >= cost.h2o;
}

function fixGlucoseFromEnvironment(environment, n) {
    if (!canFixGlucoseFromEnvironment(environment, n)) {
        return false;
    }
    const cost = fixationCost(n);
    environment.CO2Count -= cost.co2;
    environment.H2OCount -= cost.h2o;
    environment.O2Count += cost.o2;
    return true;
}

function canOxidizeGlucoseEquivalent(environment, n) {
    if (n <= 0) {
        return false;
    }
    return environment.O2Count >= STOICH.O2_PER_GLC * n;
}

function oxidizeGlucoseEquivalent(environment, n) {
    if (!canOxidizeGlucoseEquivalent(environment, n)) {
        return false;
    }
    environment.CO2Count += STOICH.CO2_PER_GLC * n;
    environment.H2OCount += STOICH.H2O_PER_GLC * n;
    environment.O2Count -= STOICH.O2_PER_GLC * n;
    return true;
}
