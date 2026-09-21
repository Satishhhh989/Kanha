import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, Color, MathUtils } from 'three';
import { KahnaUIState } from '../hooks/useKahna';

// A simple vertex shader that deforms the sphere based on time and audio intensity
const vertexShader = `
  uniform float time;
  uniform float intensity;
  varying vec3 vNormal;
  
  // Basic 3D noise function (psuedo-random)
  float hash(vec3 p) {
    p = fract(p * 0.3183099 + .1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
  }
  
  void main() {
    vNormal = normal;
    vec3 p = position;
    
    // Deform based on normal, time, and intensity
    float noise = hash(p + time * 0.5) * 2.0 - 1.0;
    float deformation = noise * intensity * 0.2;
    p += normal * deformation;
    
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }
`;

// A fragment shader for a futuristic, minimal glow
const fragmentShader = `
  uniform vec3 color;
  varying vec3 vNormal;
  
  void main() {
    // Basic fresnel effect for outer glow
    float fresnel = dot(vNormal, vec3(0.0, 0.0, 1.0));
    fresnel = clamp(1.0 - fresnel, 0.0, 1.0);
    fresnel = pow(fresnel, 2.0);
    
    // Core color mixing
    vec3 finalColor = mix(color, vec3(1.0), fresnel * 0.5);
    gl_FragColor = vec4(finalColor, 1.0);
  }
`;

interface OrbProps {
  state: KahnaUIState['agentState'];
  audioLevel: number;
}

export function Orb({ state, audioLevel }: OrbProps) {
  const meshRef = useRef<Mesh>(null);
  const materialRef = useRef<any>(null);

  // Define target states based on Agent State
  const targetColor = useMemo(() => {
    switch (state) {
      case 'IDLE': return new Color('#ffffff');
      case 'LISTENING': return new Color('#4da6ff');
      case 'TRANSCRIBING': return new Color('#60a5fa');
      case 'PROCESSING': return new Color('#a64dff');
      case 'EXECUTING': return new Color('#4dffa6');
      case 'SPEAKING': return new Color('#ffffff');
      case 'ERROR': return new Color('#ff4d4d');
      case 'DISABLED': return new Color('#666666');
      default: return new Color('#ffffff');
    }
  }, [state]);

  const targetIntensity = useMemo(() => {
    switch (state) {
      case 'IDLE': return 0.2;
      case 'LISTENING': return 0.5 + audioLevel * 0.5;
      case 'TRANSCRIBING': return 0.6;
      case 'PROCESSING': return 0.8;
      case 'EXECUTING': return 0.6;
      case 'SPEAKING': return 0.4 + audioLevel * 1.5;
      case 'ERROR': return 0.0;
      case 'DISABLED': return 0.0;
      default: return 0.2;
    }
  }, [state, audioLevel]);

  // Uniforms for the shader
  const uniforms = useMemo(
    () => ({
      time: { value: 0 },
      intensity: { value: 0.2 },
      color: { value: new Color('#ffffff') },
    }),
    []
  );

  useFrame((state) => {
    if (materialRef.current) {
      // Advance time
      materialRef.current.uniforms.time.value = state.clock.elapsedTime;
      
      // Smoothly interpolate intensity
      materialRef.current.uniforms.intensity.value = MathUtils.lerp(
        materialRef.current.uniforms.intensity.value,
        targetIntensity,
        0.1
      );

      // Smoothly interpolate color
      materialRef.current.uniforms.color.value.lerp(targetColor, 0.05);
    }

    if (meshRef.current) {
      // Gentle rotation
      meshRef.current.rotation.y += 0.005;
      meshRef.current.rotation.x += 0.002;
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[2, 64, 64]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        wireframe={state === 'DISABLED'}
        transparent={true}
      />
    </mesh>
  );
}
