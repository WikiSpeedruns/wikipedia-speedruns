import {startRun, submitRun, updateAnonymousRun} from "../game/runs.js"
import { getLocalStorageRuns, addRunToLocalStorage, setLocalStorageRuns } from "./localStorage.js"

function startLocalRun(promptId, runId) {
    const data = {
        run_id: runId,
        prompt_id: promptId,
    };

    const key = "WS-S-sprint-runs";

    addRunToLocalStorage(key, data);
}

function submitLocalRun(promptId, runId, startTime, endTime, finished, path) {
    let data = {
        prompt_id: promptId,
        start_time: startTime,
        end_time: endTime,
        finished: finished,
        path: path
    };

    let totalloadtime = -path[0]['loadTime'] + path[0]['timeReached'];
    path.forEach(function (el) {
        totalloadtime += el['loadTime']
    });
    data['play_time'] = (endTime - startTime) / 1000 - totalloadtime;

    const key = "WS-S-sprint-runs";

    let ls = getLocalStorageRuns(key);
    ls[runId] = data;
    setLocalStorageRuns(key, ls);

    //console.log(getLocalStorageRuns(key));
}

async function uploadLocalSprints() {
    const key = "WS-S-sprint-runs";
    let data = getLocalStorageRuns(key);

    const runs = Object.keys(data)
    if (runs.length == 0) return;

    let runIds = [];

    //console.log("Logged in, updating runs")

    for (let runId of runs) {
        try {
            await updateAnonymousRun(runId);
            runIds.push(runId);
            //console.log(`RUNID: ${runId}`)
        } catch (e) {
            console.log(e);
        }
    }
    //console.log("Removing sprint run cache")
    localStorage.removeItem(key);
}

function getLocalSprints() {
    const key = "WS-S-sprint-runs";
    return getLocalStorageRuns(key);
}

function getLocalRun(run_id) {
    return getLocalSprints()[run_id];
}

function promptLocallyPlayed(prompt_id) {
    const runs = getLocalSprints();
    for (const run in runs) {
        if (runs[run]['prompt_id'] === parseInt(prompt_id)) {
            return true;
        }
    }

    return false;
}

export { startLocalRun, submitLocalRun, uploadLocalSprints, getLocalSprints, getLocalRun, promptLocallyPlayed };

