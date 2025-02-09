const id = "picoCaravanControl";
const { spawn } = require('node:child_process');

let plugin = {}

module.exports = function(app, options) {
  "use strict"
  let plugin = {}
  plugin.id = id
  plugin.name = "Simarine Pico and Caravan Control to SignalK"
  plugin.description = "Read Simarine config_csl and updates from the network."

  let unsubscribes = []

  let schema = {
    properties: {
      batteryNr: {
        type: "number",
        title: "Set starting instance for batteries",
        default: 1
      },
      tankNr: {
        type: "number",
        title: "Set starting instance for tanks",
        default: 1
      },
      currentNr: {
        type: "number",
        title: "Set starting instance for current",
        default: 1
      },
      voltNr: {
        type: "number",
        title: "Set starting instance for voltages",
        default: 0
      },
      ohmNr: {
        type: "number",
        title: "Set starting instance for ohm",
        default: 1
      }
    }
  }

  plugin.schema = function() {
    return schema
  }

  let child

  plugin.start = function(options, restartPlugin) {
    app.debug('Starting plugin');

    let sensorList
    let configRead = false
    child = spawn('python3', ['pico.py'], { cwd: __dirname });

    child.stdout.on('data', function (data) {
      let dataString = data.toString()
      sensorList = JSON.parse(dataString)
      app.debug('global_sensorList: %j', sensorList)
      configRead = true
    })

    let udp = require('dgram')
    let port = 43210
    let socket = udp.createSocket('udp4')
    let element
    let sensorListTmp
    let lastUpdate
    let firstUpdate = true

    socket.on('message', function (msg, info){
      if (Date.now() - lastUpdate < 1000) {
        // One update per second
        return
      }
      lastUpdate = Date.now()
      let message = msg.toString('hex')
      // app.debug(message)
      if (configRead === true && message.length > 100 && message.length < 1000) {
        element = parseMessage(message)
        sensorListTmp = JSON.parse(JSON.stringify(sensorList))
        Object.keys(sensorList).forEach(item => {
	        // debug("global_sensorList[" + str(item_rv) + "]: " + global_sensorList[item_rv]["name"])
	        let elId = sensorList[item]['pos']
	        let type = sensorList[item]['type']
          switch (type) {
	          case 'barometer':
	            readBaro(item, elId)
              break
	          case 'thermometer':
	            readTemp(item, elId)
              break
	          case 'battery':
	            readBatt(item, elId)
              break
	          case 'ohm':
	            readOhm(item, elId)
              break
	          case 'volt':
	            readVolt(item, elId)
              break
	          case 'current':
	            readCurrent(item, elId)
              break
	          case 'tank':
	            readTank(item, elId)
              break
          }
        })
        // app.debug(sensorListTmp)
        let updates = createUpdates(sensorListTmp)
        pushDelta (updates)
      } else {
        // app.debug('Not processing: ' + message)
      }
    });

    socket.on('listening', function(){
      let address = socket.address();
      app.debug("listening on :" + address.address + ":" + address.port);
    });

    socket.bind(port, function() {
      socket.setBroadcast(true);
      const address = socket.address()
      app.debug("Client using port " + address.port)
    })

    socket.on('error', function (err) {
      app.debug('Error: ' + err)
    })

    function readBaro (sensorId, elementId) {
      sensorListTmp[sensorId]['pressure'] = element[elementId][1] + 65536
    }

    function readTemp (sensorId, elementId) {
      sensorListTmp[sensorId]['temperature'] = toTemperature(element[elementId][1])
    }

    function readTank (sensorId, elementId) {
      sensorListTmp[sensorId]['currentLevel'] = element[elementId][0] / 1000
      sensorListTmp[sensorId]['currentVolume'] = element[elementId][1] / 1000
    }

    function readVolt (sensorId, elementId) {
      let volt = element[elementId][1]
      if (volt !== 65535) {
        sensorListTmp[sensorId]['voltage'] = volt / 1000
      }
    }

    function readOhm (sensorId, elementId) {
      sensorListTmp[sensorId]['ohm'] = element[elementId][1]
    }

    function readCurrent (sensorId, elementId) {
      let current = element[elementId][1]
      if (current > 25000) {
        current = (65535 - current) / 100
      } else {
        current = current / 100 * -1
      }
      sensorListTmp[sensorId]['current'] = current
    }

    function readBatt (sensorId, elementId) {
      let stateOfCharge = Number((element[elementId][0] / 16000).toFixed(2))
      sensorListTmp[sensorId]['stateOfCharge'] = stateOfCharge
      sensorListTmp[sensorId]['capacity.remaining'] = element[elementId][1] * stateOfCharge
      sensorListTmp[sensorId]['voltage'] = element[elementId + 2][1] / 1000
      let current = element[elementId + 1][1]
      if (current > 25000) {
        current = (65535 - current) / 100
      } else {
        current = current / 100 * -1
      }
      sensorListTmp[sensorId]['current'] = current
      let timeRemaining
      if (element[elementId][0] !== 65535) {
        timeRemaining = Math.round(sensorList[sensorId]['capacity.nominal'] / 12 / ((current * stateOfCharge) + 0.001) )
      }
      if (timeRemaining < 0) {
        timeRemaining = 60*60 * 24 * 7    // One week
      }
      sensorListTmp[sensorId]['capacity.timeRemaining'] = timeRemaining
    }

    function toTemperature (temp) {
      // Unsigned to signed
      if (temp > 32768) {
        temp = temp - 65536
      }
      
      return Number((temp / 10 + 273.15).toFixed(2))
    }

    function parseMessage (hexString) {
      let result = {}
      hexString = hexString.substr(28)
      // app.debug("hexString: " + hexString)
      while (hexString.length > 4) { 
        let [field_nr, field_data, response] = getNextField(hexString)
        result[field_nr] = field_data
        hexString = response
        
      }
      return result  
    }
    
    function getNextField (hexString) {
      // app.debug("field_nr: " + hexString.substr(0,2) + " field_type: " + hexString.substr(2,2))
      let field_nr = parseInt(hexString.substr(0,2), 16)
      let field_type = parseInt(hexString.substr(2,2), 16)
      // app.debug(`field_nr: ${field_nr} field_type: ${field_type}`)
      switch (field_type) {
        case 1:
          let a = parseInt(hexString.substr(4,4), 16)
          let b = parseInt(hexString.substr(8,4), 16)
          let field_data = [a, b]
          hexString = hexString.substr(14)
          return [field_nr, field_data, hexString]
          break
        case 3:
          break
        case 4:
          // Text string
          break
      }
    }


    function pushDelta(values) {
      let update = {
        updates: [
          { 
            values: values
          }
        ]
      }
      app.debug('update: %j', update)
      app.handleEvent(plugin.id, update)

    }

    function sendMetas(metas) {
      let update = {
        updates: [
          { 
            meta: metas
          }
        ]
      }
      app.debug('update: %j', update)
      app.handleEvent(plugin.id, update)

    }

    function createUpdates (sensorList) {
	    let batteryInstance = options.batteryNr || 1
	    let currentInstance = options.currentNr || 1
	    let ohmInstance = options.ohmNr || 1
	    let voltInstance = options.voltNr || 0
	    let tankInstance = options.tankNr || 1
	    // for key, value in global_sensorList.items():
      let updates = []
      let metas = []
      for (const [key, value] of Object.entries(sensorList)) {
        // app.debug('key: %d  value: %j', key, value)
        switch (value['type']) {
	        case 'barometer':
	          updates.push({"path": "environment.inside.pressure", "value": value.pressure})
            break
	        case 'thermometer':
	          updates.push({"path": "electrical.batteries.1.temperature", "value": value.temperature})
            break
	        case 'volt':
	          updates.push({"path": "electrical.voltage." + String(voltInstance) + ".value", "value": value.voltage})
	          updates.push({"path": "electrical.voltage." + String(voltInstance) + ".name", "value": value.name})
            if (firstUpdate) {
	            metas.push({"path": "electrical.voltage." + String(voltInstance) + ".value", "value": {"units": "V"}})
            }
	          voltInstance++
            break
	        case 'ohm':
	          updates.push({"path": "electrical.ohm." + String(ohmInstance) + ".value", "value": value.ohm})
	          updates.push({"path": "electrical.ohm." + String(ohmInstance) + ".name", "value": value.name})
            if (firstUpdate) {
	            metas.push({"path": "electrical.ohm." + String(ohmInstance) + ".value", "value": {"units": "ohm"}})
            }
            ohmInstance++
            break
	        case 'current':
	          updates.push({"path": "electrical.current." + String(currentInstance) + ".value", "value": value.current})
	          updates.push({"path": "electrical.current." + String(currentInstance) + ".name", "value": value.name})
            if (firstUpdate) {
	            metas.push({"path": "electrical.current." + String(currentInstance) + ".value", "value": {"units": "A"}})
            }
	          currentInstance++
            break
	        case 'battery':
	          updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".name", "value": value.name})
	          updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".capacity.nominal", "value": value['capacity.nominal']})
	          if (value.hasOwnProperty('voltage')) {
	            updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".voltage", "value": value.voltage})
            }
	          if (value.hasOwnProperty('temperature')) {
	            updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".temperature", "value": value.temperature})
            }
	          if (value.hasOwnProperty('current')) {
		          updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".current", "value": value.current})
            }
	          if (value.hasOwnProperty('capacity.remaining')) {
		          updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".capacity.remaining", "value": value['capacity.remaining']})
		          updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".capacity.stateOfCharge", "value": value.stateOfCharge})
            }
	          if (value.hasOwnProperty('capacity.timeRemaining')) {
		          updates.push({"path": "electrical.batteries." + String(batteryInstance) + ".capacity.timeRemaining", "value": value['capacity.timeRemaining']})
			        batteryInstance++
            }
            break
			    case 'tank':
			      updates.push({"path": "tanks." + value.fluid + "." + String(tankInstance) + ".currentLevel", "value": value.currentLevel})
			      updates.push({"path": "tanks." + value.fluid + "." + String(tankInstance) + ".currentVolume", "value": value.currentVolume / 10})
			      updates.push({"path": "tanks." + value.fluid + "." + String(tankInstance) + ".name", "value": value.name})
			      updates.push({"path": "tanks." + value.fluid + "." + String(tankInstance) + ".type", "value": value.fluid_type})
			      updates.push({"path": "tanks." + value.fluid + "." + String(tankInstance) + ".capacity", "value": value.capacity / 1000})
			      tankInstance++
            break
		    }
      }
      if (firstUpdate) {
        firstUpdate = false
        sendMetas(metas)
      }
      return updates
    }
  }

  plugin.stop = function() {
    if (child) {
      process.kill(child.pid)
      child = undefined
    }
    app.debug("Stopped")
  }

  return plugin;
};
