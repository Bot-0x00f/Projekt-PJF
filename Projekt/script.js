var state;
var info;

function init(evt) {
    info = JSON.parse(evt.data);
    state = JSON.parse(evt.data)['state'];

    var LEDs = document.getElementById("LEDsList");

    for (i = 0; i < state['seg'][0].len; i++) {
        var d = document.createElement("div");
        d.textContent = i + 1;
        d.style = `background-color:rgb(${state['seg'][0].col[0][0]}, ${state['seg'][0].col[0][1]}, ${state['seg'][0].col[0][2]});
                       box-shadow: 0px 0px 21px 0px rgb(${state['seg'][0].col[0][0]}, ${state['seg'][0].col[0][1]}, ${state['seg'][0].col[0][2]})`;
        LEDs.appendChild(d);
    }

    document.getElementById("brightness").value = state['bri'];
    document.getElementById("intensity").value = state['seg'][0].ix;
    document.getElementById("speed").value = state['seg'][0].sx;
    document.getElementById("selectedColor").style = `background-color: rgb(${state['seg'][0].col[0][0]},${state['seg'][0].col[0][1]},${state['seg'][0].col[0][2]})`; //wskaŸnik koloru

    var effects = document.getElementById("effects").children[1];

    for (i = 0; i < info['effects'].length; i++) {
        var li = document.createElement("li");
        li.textContent = info['effects'][i];
        li.value = i;
        effects.appendChild(li);
    }

    var palettes = document.getElementById("palettes").children[1];

    for (i = 0; i < info['palettes'].length; i++) {
        if (i >= 1 && i <= 5) continue;
        var li = document.createElement("li");
        li.textContent = info['palettes'][i];
        li.value = i;
        palettes.appendChild(li);
    }

    currentEffect = document.getElementById("currentEffect");
    if (state["seg"][0]["fx"] > 0) {   //efekt inny od Solid
        currentEffect.children[0].innerText = "Effect: " + info["effects"][state["seg"][0]["fx"]];
        currentEffect.style.visibility = "visible";
        currentEffect.style.opacity = "1";
    }else{
        currentEffect.style.visibility = "hidden";
        currentEffect.style.opacity = "0";
    }
    
}

window.onload = function () {
    var ws;     //WebSocket
    var canvas = document.getElementById('colorCanvas');
    var canvasContext = canvas.getContext('2d');

    ws = new WebSocket("ws://localhost:8888/ws");   //Tworzenie po³¹czenia

    ws.onopen = function (e) {                      //Po³¹czono pomyœlnie, inicjalizacja parametrów na stronie
        console.log("***Connection Opened***");
        ws.send(`state`);
    };

    var LEDs = document.getElementById("LEDsList");

    ws.onmessage = function (evt) {                 //odbieranie wiadomoœci
        var data = JSON.parse(evt.data);
        if (data["cmd"] == "state") {
            init(evt);
            return;
        }
        else if (data["cmd"] == "lv")               //dane dotycz¹ce obecnego stanu ledów
        {                  
            console.log('data["cmd"] = ' + data["cmd"]);
            var temp = 0
            var r, g, b;
            for (i = 0; i < info["state"]["seg"][0].len; i++) {
                temp = parseInt("0x" + data["leds"][i]);
                r = (temp >> 16) & 0xFF;
                g = (temp >> 8) & 0xFF;
                b = temp & 0xFF;
                LEDs.children[i].style = `background-color:rgb(${r}, ${g}, ${b});
                       box-shadow: 0px 0px 21px 0px rgb(${r}, ${g}, ${b})`;
            }
        }
        
    };

    let gradient = canvas.getContext('2d').createLinearGradient(0, 0, canvas.width, 0)
    gradient.addColorStop(0, '#ff0000')
    gradient.addColorStop(1 / 6, '#ffff00')
    gradient.addColorStop((1 / 6) * 2, '#00ff00')
    gradient.addColorStop((1 / 6) * 3, '#00ffff')
    gradient.addColorStop((1 / 6) * 4, '#0000ff')
    gradient.addColorStop((1 / 6) * 5, '#ff00ff')
    gradient.addColorStop(1, '#ff0000')
    canvas.getContext('2d').fillStyle = gradient
    canvas.getContext('2d').fillRect(0, 0, canvas.width, canvas.height)

    gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, canvas.height)
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1)')
    gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0)')
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
    canvas.getContext('2d').fillStyle = gradient
    canvas.getContext('2d').fillRect(0, 0, canvas.width, canvas.height)

    gradient = canvas.getContext('2d').createLinearGradient(0, 0, 0, canvas.height)
    gradient.addColorStop(0, 'rgba(0, 0, 0, 0)')
    gradient.addColorStop(0.5, 'rgba(0, 0, 0, 0)')
    gradient.addColorStop(1, 'rgba(0, 0, 0, 1)')
    canvas.getContext('2d').fillStyle = gradient
    canvas.getContext('2d').fillRect(0, 0, canvas.width, canvas.height)
    
    //zmiana koloru
    canvas.onmousemove = canvas.onmousedown = function (e) {
        if (e.buttons == 1) {
            var imgData = canvasContext.getImageData((e.offsetX / canvas.clientWidth) * canvas.width, (e.offsetY / canvas.clientHeight) * canvas.height, 1, 1)
            var rgba = imgData.data;
            document.getElementById("redC").value = rgba[0];
            document.getElementById("greenC").value = rgba[1];
            document.getElementById("blueC").value = rgba[2];
            document.getElementById("selectedColor").style = `background-color: rgb(${rgba[0]},${rgba[1]},${rgba[2]})`; //wskaŸnik koloru
            for (i = 0; i < info["state"]["seg"][0].len; i++) {
                LEDs.children[i].style = `background-color:rgb(${rgba[0]}, ${rgba[1]}, ${rgba[2]});
                       box-shadow: 0px 0px 21px 0px rgb(${rgba[0]}, ${rgba[1]}, ${rgba[2]})`;
            }
            ws.send(`col ${rgba[0]} ${rgba[1]} ${rgba[2]}`);
        }
    }

    var Rinput = document.getElementById("redC");
    var Ginput = document.getElementById("greenC");
    var Binput = document.getElementById("blueC");

    Rinput.oninput = Ginput.oninput = Binput.oninput = function (e) {
        document.getElementById("selectedColor").style = `background-color: rgb(${Rinput.value},${Ginput.value},${Binput.value})`; //wskaŸnik koloru
        ws.send(`col ${Rinput.value} ${Ginput.value} ${Binput.value}`);
    }

    var onOff = document.getElementById("onOff");

    onOff.onmousedown = function (e) {
        ws.send(`onoff`);
    }

    //zmiana jasnoœci
    var brightInput = document.getElementById("brightness");

    brightInput.onchange = function (e) {
        ws.send(`bri ${brightInput.value}`);
    }

    //szybkosc efektu
    var speedInput = document.getElementById("speed");

    speedInput.onchange = function (e) {
        ws.send(`spd ${speedInput.value}`);
    }

    //intensywnoœæ efektu
    var intensInput = document.getElementById("intensity");

    intensInput.onchange = function (e) {
        ws.send(`intens ${intensInput.value}`);
    }

    //wybór efektu
    effectsList = document.getElementById("effects");

    effectsList.onmousedown = function (e) {
        if (typeof (e.target.value) != 'undefined') {
            effects = info["effects"];
            currentEffect = document.getElementById("currentEffect");
            if (e.target.value > 0) {   //efekt inny od Solid
                currentEffect.children[0].innerText = "Effect: " + effects[e.target.value];
                currentEffect.style.visibility = "visible";
                currentEffect.style.opacity = "1";
            } else {
                currentEffect.style.visibility = "hidden";
                currentEffect.style.opacity = "0";
            }
            ws.send(`fx ${e.target.value}`);
        }
    }

    //wybór palety
    palettesList = document.getElementById("palettes");

    palettesList.onmousedown = function (e) {
        if (typeof (e.target.value) != 'undefined') {
            ws.send(`pal ${e.target.value}`);
        }
    }

    //wybór predefiniowanego koloru
    colorPresets = document.getElementById("colorPresets");

    colorPresets.onmousedown = function (e) {
        document.getElementById("selectedColor").style.backgroundColor = e.target.style.backgroundColor;
        ws.send(`col ${e.target.children[0].innerText}`);
    }

    document.getElementById("btnMic").onmousedown = function (e) {
        ws.send("mic");
    }

    //USTAWIENIA
    //ustawienie adresu IP urzadzenia
    document.getElementById("apply1").onclick = function (e) {
        temp = document.getElementById("setAddress");
        addressPattern = /^[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}$/;
        if (addressPattern.test(temp.value)) {
            temp.style = "border: inherit";
            ws.send("set address " + temp.value);
        } else {
            temp.style = "border: solid 4px red";
        }
    }
        
    //ustawienie ilosci LEDow
    document.getElementById("apply2").onclick = function (e) {
        temp = document.getElementById("setLEDsAmount");
        if (temp.value >= 0) {
            temp.style = "border: inherit";
            ws.send("set ledsamount " + temp.value);
        } else {
            temp.style = "border: solid 4px red";
        }
    }
}

