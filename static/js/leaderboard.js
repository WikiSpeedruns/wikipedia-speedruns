import { serverData } from "./modules/serverData.js"
import { fetchJson } from "./modules/fetch.js"

import { pathArrowFilter } from "./modules/game/filters.js";

const URL_PROMPT_ID = serverData["prompt_id"];
const URL_LOBBY_ID = serverData["lobby_id"] || null;

const DEFAULT_PAGE_SIZE = 20;

Vue.filter('pathArrow', pathArrowFilter)

var LeaderboardRow = {
    props: [
        "run",
        "currentRunId"
    ],

    data: function() {
        return {
            lobbyId: URL_LOBBY_ID,
        }
    },

    template: (`
        <tr>
            <td>{{run.rank}}</td>

            <td class="l-col" v-if="run.username">
                <strong v-if="run.run_id == currentRunId">{{run.username}}</strong>
                <span v-else>{{run.username}}</span>
            </td>
            <td class="l-col" v-else-if="run.name">
                <strong v-if="run.run_id == currentRunId">{{run.name}}</strong>
                <span v-else>{{run.name}}</span>
            </td>
            <td v-else><strong>You</strong></td>

            <td class="l-col">{{(run.play_time).toFixed(3)}} s</td>
            <td>{{run.path.length}}</td>

            <td style="min-width:400px">
                {{run.path | pathArrow}}
                <a v-if="!lobbyId" v-bind:href="'/replay?run_id=' + run.run_id" target="_blank" title="Replay" >
                    <i class="bi bi-play"></i>
                </a>
            </td>
        </tr>
    `)
}



function populateGraph(runs, runId) {

    function componentToHex(c) {
        var hex = c.toString(16);
        return hex.length == 1 ? "0" + hex : hex;
    }

    function rgbToHex(r, g, b) {
        return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
    }


    var graph = new Springy.Graph();

    var nodes = [];
    var edges = [];

    var checkIncludeLabels = function(label, array) {
        for (let i = 0; i < array.length; i++) {
            if (array[i].label === label) {
                return i;
            }
        }
        return -1;
    }

    var checkIncludeEdgeLabels = function(src, dest, array) {
        for (let i = 0; i < array.length; i++) {
            if (array[i].src === src && array[i].dest === dest) {
                return i;
            }
        }
        return -1;
    }

    var startNode;
    var endNode;


    for (let i = 0; i < runs.length; i++) {
        var pathNodes = runs[i]["path"]
        var cur = (runs[i]["run_id"] === Number(runId)) ? true : false;

        for (let j = 0; j < pathNodes.length; j++) {
            const article = pathNodes[j]["article"]

            var index = checkIncludeLabels(article, nodes);
            if (index === -1) {
                let node = {type: 0, label: article, count: 1, current: cur};
                if (j === 0) {
                    node.type = 1;
                    startNode = node;
                }
                else if (j === pathNodes.length - 1) {
                    node.type = 2;
                    endNode = node;
                }
                else if (node.label !== startNode.label){
                    node.type = 0;
                    nodes.push(node);
                }

                //let node = {type: type, label: pathNodes[j], count: 1, current: cur};
                //nodes.push(node);

            } else {
                if (cur) {
                    nodes[index].current = cur;
                }
                nodes[index].count = nodes[index].count + 1;
            }
        }
    }

    if (runs.length > 0) {
        nodes.push(startNode);
        nodes.push(endNode);
    }


    for (let i = 0; i < runs.length; i++) {
        var pathNodes = runs[i]["path"]
        var cur = (runs[i]["run_id"] === Number(runId)) ? true : false;

        for (let j = 0; j < pathNodes.length - 1; j++) {
            const u = pathNodes[j]["article"]
            const v = pathNodes[j + 1]["article"]

            let index = checkIncludeEdgeLabels(u, v, edges);

            if (index === -1) {
                let edge = {src: u, dest: v, count: 1, current: cur};
                edges.push(edge);
            } else {
                if (cur) {
                    edges[index].current = cur;
                }
                edges[index].count = edges[index].count + 1;
            }
        }
    }

    var edgeCountMax = 0;
    var nodeCountMax = 0;
    var nodeObj = [];
    var nodeLabels = [];

    nodes.forEach(function(node) {
        if (node.count > nodeCountMax) {
            nodeCountMax = node.count;
        }
    })
    nodes.forEach(function(node) {
        var color;
        var font;
        var textheight;

        if (node.type === 1) {
            color = "#008000";
            font= "bold 15px Verdana, sans-serif";
            textheight = 18;
        } else if (node.type === 2) {
            color = "#FF5733";
            font= "bold 15px Verdana, sans-serif";
            textheight = 18;
        } else {
            color = "#000000";
            font= "10px Verdana, sans-serif";
            textheight = 10;
        }

        var color = (node.current && node.type !== 1 && node.type !== 2) ? "#ff9700" : color;
        var weightScale;
        if (nodeCountMax === 1) {
            weightScale = 12;
        } else {
            weightScale = 12 / (nodeCountMax - 1) * (node.count - 1) + 6; //map from 6 to 18
        }

        var n = graph.newNode({label: node.label, color: color, font: font, textheight: textheight, type: node.type, weightScale: weightScale, count: node.count});
        nodeObj.push(n);
        nodeLabels.push(node.label);

    })

    edges.forEach(function(edge) {
        if (edge.count > edgeCountMax) {
            edgeCountMax = edge.count;
        }
    })

    edges.forEach(function(edge) {
        var srcIndex = nodeLabels.indexOf(edge.src);
        var destIndex = nodeLabels.indexOf(edge.dest);
        var colorScale;
        var weightScale;

        if (edgeCountMax === 1) {
            colorScale = 255;
            weightScale = 2.25;
        } else {
            colorScale = parseInt(255 - (255 / (edgeCountMax - 1)) * (edge.count - 1), 10);
            weightScale = 1.5 / (edgeCountMax - 1) * (edge.count - 1) + 1.5; //map from 1.5 to 3
        }

        var color = edge.current ? "#ff9700" : rgbToHex(255 - colorScale, 0, colorScale);
        graph.newEdge(nodeObj[srcIndex], nodeObj[destIndex], {color: color, label: edge.count, weight: weightScale});


    })


    return graph;
}



var app = new Vue({
    delimiters: ['[[', ']]'],
    el: '#app',
    data: {
        prompt: {},
        available: false,

        runs: [],
        numRuns: 0,

        runId: -1,
        currentRun: null,
        currentRunPosition: 0,

        promptId: URL_PROMPT_ID,
        lobbyId: URL_LOBBY_ID,

        // Search params default values
        limit: 20,
        offset: 0,


    },

    computed: {
        page: function() { return Math.floor(this.offset / this.limit); },
        numPages: function() { return Math.max(1, Math.ceil(this.numRuns / this.limit)); }
    },

    components: {
        'leaderboard-row': LeaderboardRow
    },


    methods : {
        genGraph: function () {
            var graph = populateGraph(this.runs, this.runId);
            $('#springydemo').springy({ graph: graph });
        },


        sortStatus: function(tab) {
            if (this.sortMode === tab) {
                return `<i class="bi bi-chevron-down"></i>`
            }
            return `<i class="bi bi-dash-lg"></i>`
        },



        goToPage: function(newPage)
        {
            let url = new URL(window.location.href);
            url.searchParams.set('offset', newPage * this.limit);
            url.searchParams.set('limit', this.limit);
            window.location.replace(url);
        },


        setSort: function(tab) {
            let url = new URL(window.location.href);
            url.searchParams.set('sort_mode', tab);
            window.location.replace(url);
        },

        setTimeFilter: function(f) {
            if (f != this.timeFilter) {
                let url = new URL(window.location.href)
                url.searchParams.set('played', f)
                window.location.replace(url)
            }
        },


    },

    created: async function() {
        /* Parse url params */
        let url = new URL(window.location.href);

        this.offset = Number(url.searchParams.get('offset') || 0);
        this.limit = Number(url.searchParams.get('limit') || DEFAULT_PAGE_SIZE);

        /* TODO find this by user if not provided in urlParams */
        this.runId = Number(url.searchParams.get("run_id")) || -1;

        /* Make query */
        let path = this.lobbyId === null
            ? `/api/sprints/${this.promptId}/leaderboard`
            : `/api/lobbys/${this.lobbyId}/prompts/${this.promptId}/leaderboard`;

        if (this.runId !== -1) {
            path += "/" + this.runId;
        }


        let resp = await (await fetchJson(path, "POST", {
            "limit": this.limit,
            "offset": this.offset
        })).json();



        /* Fill data structures */
        this.available = !('available' in resp['prompt']) || resp["prompt"]["available"];
        this.prompt = resp["prompt"];
        this.runs = resp["runs"];
        this.numRuns = resp["numRuns"];

        // Find current run
        const currRunIndex = this.runs.findIndex((run) => run["run_id"] === this.runId)
        if (currRunIndex !== -1) {
            this.currentRun = this.runs[currRunIndex];

            // check if current run does not fall within range, remove and set positon if so
            if (this.currentRun['rank'] - 1 < this.offset) {
                this.currentRunPosition = -1 ;
                this.runs.splice(currRunIndex, 1);
            } else if (this.currentRun['rank'] - 1 >= this.offset + this.limit) {
                this.currentRunPosition = 1;
                this.runs.splice(currRunIndex, 1);
            }
        }




        this.genGraph();
    }
})