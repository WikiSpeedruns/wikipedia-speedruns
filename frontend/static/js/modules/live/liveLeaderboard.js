// A very simple websocker client to signal people finishing a prompt
// and to tell the leaderboard to update

const wsServer = "ws://localhost:8000";

function triggerLeaderboardUpdate(lobbyId, promptId) {
    let ws = new WebSocket(wsServer);

    ws.onopen = (event) => {
        console.log("Test");

        ws.send(JSON.stringify({
            type: "update",
            lobby_id: lobbyId,
            prompt_id: promptId
        }));

        ws.close();
    }
};

class LiveLeaderboardHelper {
    constructor(lobbyId, promptId, updateCallback) {
        this.ws = new WebSocket(wsServer);

        this.ws.onopen = (event) => {
            this.ws.send(JSON.stringify({
                type: "leaderboard",
                lobby_id: lobbyId,
                prompt_id: promptId
            }));
        }

        this.ws.onmessage = (event) => {
            if (event.data === "refresh") {
                updateCallback()
            }
        };
    }
}

export {triggerLeaderboardUpdate, LiveLeaderboardHelper};