class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(url = 'ws://localhost:8000/ws') {
    if (this.socket) {
      this.disconnect();
    }

    try {
      this.socket = new WebSocket(url);
      
      this.socket.onopen = () => {
        console.log('Connected to WebSocket server');
        this.reconnectAttempts = 0;
      };

      this.socket.onclose = () => {
        console.log('Disconnected from WebSocket server');
        this.attemptReconnect(url);
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const callback = this.listeners.get(data.type);
          if (callback) {
            callback(data);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      return this.socket;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      return null;
    }
  }

  attemptReconnect(url) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(url);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  on(event, callback) {
    this.listeners.set(event, callback);
  }

  off(event) {
    this.listeners.delete(event);
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

export default new WebSocketService();
