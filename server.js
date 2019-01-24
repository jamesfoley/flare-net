// Import WS
const uuid = require('uuid')

const WebSocket = require('ws')

// Create new websocket server
const wss = new WebSocket.Server({ port: 8080 })

const groups = {}

// Listen on connection
wss.on('connection', function connection(ws) {
  ws.id = uuid.v4()
  console.log(`Client connected ${ws.id}`)
  let groupKey = ''

  console.log(ws.id)

  ws.send(JSON.stringify({
    command: 'new_id',
    id: ws.id
  }))

  // Listen on message
  ws.on('message', function incoming(message) {
    // Decode message, must be json
    const content = JSON.parse(message)

    // switch on command
    switch(content.command) {
      case 'join_group':
        groupKey = content.data.key
        if (!groups[groupKey]) groups[groupKey] = []
        groups[groupKey].push(ws)
        console.log(groups[groupKey].length)
        break

      case 'view_change':
        if (groups[groupKey]) {
          groups[groupKey].forEach((client) => {
            client.send(JSON.stringify({
              command: 'new_view',
              view: content.data.view,
              source: ws.id
            }))
          })
        }

    }
  })

  ws.on('close', function close(ws) {
    let index = groups[groupKey].indexOf(ws)
    groups[groupKey].splice(index, 1)
    console.log(groups[groupKey].length)
  })
})
