import { Canvas } from '@react-three/fiber';
import { Orb } from './components/Orb';
import { useKahna } from './hooks/useKahna';

function App() {
  const { state } = useKahna();

  return (
    <div className="relative w-full h-screen bg-black overflow-hidden flex flex-col items-center justify-center">
      
      {/* 3D Canvas Background */}
      <div className="absolute inset-0">
        <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <Orb state={state.agentState} audioLevel={state.audioMetrics.level} />
        </Canvas>
      </div>

      {/* Foreground UI Layer */}
      <div className="relative z-10 flex flex-col items-center justify-between w-full h-full p-8 pointer-events-none">
        
        {/* Top: Status / Connections */}
        <div className="w-full flex justify-between items-start text-xs font-mono text-white/50 tracking-widest">
          <div className="flex flex-col gap-1">
            <span className={state.connection === 'CONNECTED' ? 'text-green-500/80' : 'text-red-500/80'}>
              {state.connection}
            </span>
            <span>{state.agentState}</span>
          </div>
          <div>
            {state.permissionRequest && (
              <span className="text-yellow-500/80 bg-yellow-500/10 px-2 py-1 rounded">
                NEEDS PERMISSION: {state.permissionRequest}
              </span>
            )}
          </div>
        </div>

        {/* Center: Task Visualization (if active) */}
        <div className="flex flex-col items-center gap-2">
          {state.task && (
            <div className="bg-white/5 backdrop-blur-md px-4 py-2 rounded-lg border border-white/10 flex flex-col items-center text-sm text-white/80 transition-all">
              <span className="font-semibold">{state.task.name}</span>
              <span className="text-xs text-white/50">{state.task.progress}</span>
            </div>
          )}
        </div>

        {/* Bottom: Captions & Transcripts */}
        <div className="w-full max-w-2xl text-center flex flex-col justify-end items-center gap-4 min-h-[120px]">
          {/* User Transcript (what they said) */}
          <p className="text-lg text-white/40 italic font-light transition-opacity duration-300">
            {state.transcript && `"${state.transcript}"`}
          </p>
          
          {/* KAHNA Caption (what it is saying) */}
          <p className="text-2xl text-white/90 font-medium tracking-wide drop-shadow-lg transition-all duration-300 min-h-[40px]">
            {state.caption}
          </p>

          {/* Error Message */}
          {state.error && (
            <div className="text-red-400 text-sm bg-red-900/20 px-4 py-2 rounded">
              {state.error}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;
