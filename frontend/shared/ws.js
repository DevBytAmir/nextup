function connectWs(onMessage) {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.addEventListener("message", (event) => {
    onMessage(JSON.parse(event.data));
  });
  ws.addEventListener("close", () => {
    setTimeout(() => connectWs(onMessage), 1000);
  });
  return ws;
}
