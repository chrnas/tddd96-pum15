// Establish a connection to the WebSocket server
const socket = io();

const canvas = document.getElementById('waveform');
const canvasCtx = canvas.getContext('2d');

const perf_counter = performance.now() / 1000
let clockOffset=0

document.getElementById('connectBtn').addEventListener('click', async function () {
    let name = document.getElementById('nameInput').value;
    //let xCoordinate = document.getElementById('xInput').value;
    //let yCoordinate = document.getElementById('yInput').value;

    //if (!name) {
    //    alert('Please enter your name.');
    //    return;
    //}
    //
    // Inform the server of the new user and their coordinates and send the time synchronization request
    socket.emit('newUser',false);
    syncTime();

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        const audioContext = new AudioContext();

        // Check if the AudioContext is in a suspended state (this is particularly important for Safari on iOS)
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        source.connect(analyser);
        analyser.fftSize = 2048;

        function drawLocalWaveform() {
            // Draws the local waveform of the audio input, turn off if not needed
            requestAnimationFrame(drawLocalWaveform);
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            analyser.getByteTimeDomainData(dataArray);

            canvasCtx.fillStyle = 'rgb(200, 200, 200)';
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
            canvasCtx.lineWidth = 1;
            canvasCtx.strokeStyle = 'rgb(0, 0, 0)';
            canvasCtx.beginPath();

            let sliceWidth = canvas.width * 1.0 / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                let v = dataArray[i] / 128.0;
                let y = v * canvas.height / 2;
                if (i === 0) {
                    canvasCtx.moveTo(x, y);
                } else {
                    canvasCtx.lineTo(x, y);
                }
                x += sliceWidth;
            }

            canvasCtx.lineTo(canvas.width, canvas.height / 2);
            canvasCtx.stroke();
        }

        drawLocalWaveform();

        const processor = audioContext.createScriptProcessor(2048, 1, 1);
        source.connect(processor);
        processor.connect(audioContext.destination);

        let lastTriggeredTime = null;
        const debounceInterval = 300; // Debounce interval in milliseconds, This is very bad practice, but it is a quick fix for the issue. Can cause timestamps to become unaligned. 
        const soundThreshold = 0.15; // RMS threshold for sound detection, need to be tuned
        // Maybe just use a threshhold value for amplitude instead of the RMS value since RMS will be delayed
        function calculateRMS(buffer) {
            let sum = 0;
            for (let i = 0; i < buffer.length; i++) {
                sum += buffer[i] * buffer[i];
            }
            return Math.sqrt(sum / buffer.length);
        }

        processor.onaudioprocess = function (e) {
            // Send audio data to the server when a sound is detected
            // Currently turned off as sockets are used
            const inputBuffer = e.inputBuffer.getChannelData(0);
            const dataToSend = Array.from(inputBuffer);
            const rms = calculateRMS(inputBuffer);
            now = performance.now()
            
            if (rms > 0) {
                //if (!lastTriggeredTime || now - lastTriggeredTime > debounceInterval) {
                //console.log(inputBuffer)
                const timestamp = performance.now() / 1000 - perf_counter + clockOffset;
                //socket.emit('audioData', { name: name, timestamp: timestamp, data: dataToSend }); 
                lastTriggeredTime = now;
                //}
            }
        };

    } catch (err) {
        console.error('Error accessing the microphone', err);
    }
});

let clientSendTime
// Function to initiate clock synchronization
function syncTime() {
    const clientTime  = performance.now() / 1000 - perf_counter + clockOffset; // Use performance.now() for high-resolution time
    clientSendTime = clientTime; // Use performance.now() for high-resolution time
    socket.emit('syncTime')
}

// Handle server's response for time synchronization
socket.on('syncResponse', (serverTimestamp) => {

    const clientTime =  performance.now() / 1000 - perf_counter + clockOffset; // Use performance.now() for high-resolution time

    const roundTripTime = clientTime - clientSendTime

    const serverTime = serverTimestamp; 

    const estimatedServerTime = serverTime + roundTripTime / 2;

    // Update the clock offset (adjustment needed to align client clock with server clock)
    clockOffset = estimatedServerTime - clientTime;
    console.log(`Clock offset: ${clockOffset} milliseconds. Adjust your clock accordingly.`);
});

function drawGrid() {
    // Draws the zoomed-in grid
    const gridSize = 1; // Smaller grid size for a zoomed-in effect
    const numLinesX = gridnetCanvas.width / gridSize;
    const numLinesY = gridnetCanvas.height / gridSize;

    gridCtx.strokeStyle = '#e0e0e0'; // Light grey lines for the grid

    // Draw vertical lines
    for (let i = 0; i <= numLinesX; i++) {
        gridCtx.beginPath();
        gridCtx.moveTo(i * gridSize, 0);
        gridCtx.lineTo(i * gridSize, gridnetCanvas.height);
        gridCtx.stroke();
    }

    // Draw horizontal lines
    for (let i = 0; i <= numLinesY; i++) {
        gridCtx.beginPath();
        gridCtx.moveTo(0, i * gridSize);
        gridCtx.lineTo(gridnetCanvas.width, i * gridSize);
        gridCtx.stroke();
    }

    // Optionally draw origin lines if needed
}




socket.on('soundSource', (location) => {
    const [x, y] = location;
    console.log(`Sound detected at (${x}, ${y}), plotting on the grid.`);

    plotPoint(x * 10, y * 10, '#0000ff'); // Example using blue color
});


function drawIncomingWaveform(dataArray, id, name) {
    // Draws the incoming waveform from other users. Currently turned off for performance reasons in the server
    let canvasId = 'canvas-' + id;
    let newCanvas = document.getElementById(canvasId);

    if (!newCanvas) {
        let container = document.createElement('div');
        container.className = 'audio-container';

        newCanvas = document.createElement('canvas');
        newCanvas.id = canvasId;
        newCanvas.className = 'audio-canvas';
        newCanvas.width = canvas.width;
        newCanvas.height = 100;

        let nameTag = document.createElement('div');
        nameTag.textContent = name;

        container.appendChild(nameTag);
        container.appendChild(newCanvas);
        document.getElementById('canvasContainer').appendChild(container);
    }

    let newCanvasCtx = newCanvas.getContext('2d');
    newCanvasCtx.clearRect(0, 0, newCanvas.width, newCanvas.height);
    newCanvasCtx.lineWidth = 1;
    newCanvasCtx.strokeStyle = 'rgb(255, 0, 0)';
    const sliceWidth = newCanvas.width / dataArray.length;
    let x = 0;

    newCanvasCtx.beginPath();
    for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] / 128.0;
        let y = v * 10000 + 50; // Adjusted for visibility
        if (i === 0) {
            newCanvasCtx.moveTo(x, y);
        } else {
            newCanvasCtx.lineTo(x, y);
        }
        x += sliceWidth;
    }
    newCanvasCtx.stroke();
}

function plotPoint(x, y, color = "#ff0000") { // Default color set to red
    const pointSize = 5; // Size of the point
    gridCtx.fillStyle = color; // Use the color parameter
    
    // Translate coordinates for the zoomed-in grid
    const centerX = gridnetCanvas.width / 2;
    const centerY = gridnetCanvas.height / 2;
    const translatedX = centerX + (x*2); // Adjusting the scale for zoomed-in grid
    const translatedY = centerY - (y*2); // Adjusting the scale for zoomed-in grid
    
    
    gridCtx.beginPath();
    gridCtx.arc(translatedX, translatedY, pointSize, 0, 2 * Math.PI);
    gridCtx.fill();
}


socket.on('incomingAudioData', (payload) => {
    // Handle incoming audio data from other users
    const { id, data, name } = payload;
    if (id !== socket.id) {
        drawIncomingWaveform(data, id, name);
    }
});

const gridnetCanvas = document.getElementById('gridnet'); // Ensure this canvas element exists in your HTML
const gridCtx = gridnetCanvas.getContext('2d');


socket.on('updatePositions', (users) => {
    // Listen for 'updatePositions' event from the server, TODO implement drawing of where sound is detected

    gridCtx.clearRect(0, 0, gridnetCanvas.width, gridnetCanvas.height);

    drawGrid();
    // Optionally redraw the grid here if needed

    // Plot each user's position on the grid
    users.forEach((user) => {
        plotPoint(user.xCoordinate * 10, user.yCoordinate * 10, '#22222'); // Adjust scaling factor as needed
    });
});