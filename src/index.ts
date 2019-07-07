var leftPWM: HTMLProgressElement;
var rightPWM: HTMLProgressElement;
var lagDiv: HTMLDivElement;
var statDiv: HTMLDivElement;

var commandSocket: WebSocket;
var telemetrySocket: WebSocket;

var gamepad: Gamepad;

var controls = {
    fwd: 0,
    bck: 0,
    left: 0,
    right: 0
}
var latency = -100000000000

function getWebSocketURI(socketName) {
    var loc = window.location, new_uri;
    if (loc.protocol === 'https:') {
        new_uri = 'wss:';
    } else {
        new_uri = 'ws:';
    }
    new_uri += '//' + loc.host;
    new_uri += loc.pathname + socketName;
    return new_uri
}

function init() {
    setupGamepad();

    leftPWM = <HTMLProgressElement>document.getElementById('left_pwm')
    rightPWM = <HTMLProgressElement>document.getElementById('right_pwm')
    lagDiv = <HTMLDivElement>document.getElementById('lag_div')
    statDiv = <HTMLDivElement>document.getElementById('stat_div')

    document.addEventListener("keydown", keyDown);
    document.addEventListener("keyup", keyUp);

    commandSocket = new WebSocket(getWebSocketURI("ws/command"));
    telemetrySocket = new WebSocket(getWebSocketURI("ws/telemetry"));
    telemetrySocket.onmessage = updateTelemetry;

    setInterval(update, 50);
}
function updateTelemetry(event) {
    var blob = JSON.parse(event.data);
    statDiv.innerHTML = "READY/RUNNING";
    statDiv.style.color = "lightgreen";
    leftPWM.value = 100 * Math.abs(blob['left']);
    rightPWM.value = 100 * Math.abs(blob['right']);
    var currentTime = Date.now()
    var lastTime = blob['last_command']
    latency = (latency * 0.95) + ((currentTime - lastTime) * 0.05)
    lagDiv.innerHTML = Math.max(Math.ceil(latency), 0) + " ms";

}
function keyDown(event: KeyboardEvent) {
    let key = event.keyCode;
    controls.left = key == 65 || key == 37 ? 1 : controls.left;
    controls.right = key == 68 || key == 39 ? 1 : controls.right;
    controls.fwd = key == 87 || key == 38 ? 1 : controls.fwd;
    controls.bck = key == 83 || key == 40 ? 1 : controls.bck;
}

function keyUp(event: KeyboardEvent) {
    let key = event.keyCode;
    controls.left = key == 65 || key == 37 ? 0 : controls.left;
    controls.right = key == 68 || key == 39 ? 0 : controls.right;
    controls.fwd = key == 87 || key == 38 ? 0 : controls.fwd;
    controls.bck = key == 83 || key == 40 ? 0 : controls.bck;
}

function gamepadUpdate(){
    if(gamepad){
        console.log("FWD "+gamepad.axes[1] + " LR "+gamepad.axes[0]);
    }
}

function update() {
    if (telemetrySocket.readyState == telemetrySocket.CLOSED) {
        lagDiv.innerHTML = "∞"
        lagDiv.style.color = "darkred"
        statDiv.innerHTML = "HALT/DISCONNECTED"
        statDiv.style.color = "darkred"
    }
    gamepadUpdate();
    sendCommand();
}

function sendCommand() {
    let left = controls.fwd - controls.bck + controls.right - controls.left;
    let right = controls.fwd - controls.bck + controls.left - controls.right;
    //console.log("L " + controls.left + " R " + controls.right + " FWD " + controls.fwd + " BCK " + controls.bck);
    commandSocket.send(
        JSON.stringify({
            'left': left,
            'right': right,
            'time': Date.now()
        }))
}

function setupGamepad() {
    window.addEventListener("gamepadconnected", function (e: GamepadEvent) {
        console.log("Gamepad connected at index %d: %s.", e.gamepad.index, e.gamepad.id);
        gamepad = navigator.getGamepads()[e.gamepad.index];
    });
}