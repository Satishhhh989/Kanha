import { useState, useEffect, useCallback } from 'react';

export type KahnaUIState = {
  connection: 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED' | 'ERROR';
  agentState: 'IDLE' | 'LISTENING' | 'TRANSCRIBING' | 'PROCESSING' | 'EXECUTING' | 'SPEAKING' | 'ERROR' | 'DISABLED';
  transcript: string;
  caption: string;
  task: { name: string; progress: string } | null;
  audioMetrics: { level: number; rms: number };
  permissionRequest: string | null;
  error: string | null;
};

const initialState: KahnaUIState = {
  connection: 'DISCONNECTED',
  agentState: 'IDLE',
  transcript: '',
  caption: '',
  task: null,
  audioMetrics: { level: 0, rms: 0 },
  permissionRequest: null,
  error: null,
};

export function useKahna(wsUrl: string = 'ws://localhost:8765/ws') {
  const [state, setState] = useState<KahnaUIState>(initialState);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connect = useCallback(() => {
    setState((s) => ({ ...s, connection: 'CONNECTING' }));
    
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      setState((s) => ({ ...s, connection: 'CONNECTED', error: null }));
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleKahnaEvent(data);
      } catch (err) {
        console.error('Failed to parse WS message', err);
      }
    };
    
    socket.onclose = () => {
      setState((s) => ({ ...s, connection: 'DISCONNECTED' }));
      // Attempt reconnect after 3s
      setTimeout(connect, 3000);
    };
    
    socket.onerror = (err) => {
      setState((s) => ({ ...s, connection: 'ERROR', error: 'WebSocket connection failed' }));
      console.error('WebSocket Error', err);
    };
    
    setWs(socket);
  }, [wsUrl]);

  useEffect(() => {
    connect();
    return () => {
      if (ws) ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleKahnaEvent = (event: any) => {
    const { event_type, payload } = event;
    
    setState((s) => {
      const nextState = { ...s };
      
      switch (event_type) {
        case 'AGENT_STATE_CHANGED':
          nextState.agentState = payload.state;
          if (payload.state === 'IDLE') {
            nextState.caption = '';
            nextState.task = null;
          }
          break;
        case 'TRANSCRIPT_PARTIAL':
        case 'TRANSCRIPT_FINAL':
          nextState.transcript = payload.text;
          break;
        case 'TTS_TEXT':
          nextState.caption = payload.text;
          break;
        case 'TTS_AUDIO_LEVEL':
          nextState.audioMetrics = { level: payload.level, rms: payload.rms };
          break;
        case 'TASK_STARTED':
          nextState.task = { name: payload.name, progress: 'STARTED' };
          break;
        case 'TASK_PROGRESS':
          if (nextState.task) {
            nextState.task.progress = payload.progress;
          }
          break;
        case 'TASK_COMPLETED':
        case 'TASK_FAILED':
          nextState.task = null;
          break;
        case 'PERMISSION_REQUIRED':
          nextState.permissionRequest = payload.permission;
          break;
        case 'AGENT_ERROR':
          nextState.error = payload.error;
          nextState.agentState = 'ERROR';
          break;
      }
      
      return nextState;
    });
  };

  const sendCommand = (cmd: any) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(cmd));
    }
  };

  return { state, sendCommand };
}
