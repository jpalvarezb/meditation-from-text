'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial } from '@react-three/drei';
import { Suspense, useRef, useState, CSSProperties, useEffect } from 'react';
import { Mesh, Group, Vector3 } from 'three';
import { useRouter } from 'next/navigation';

function AnimatedOrb({
  tapped,
  transitioning,
  reversing,
  onReach,
  onSphereClick,
  distortion,
}: {
  tapped: boolean;
  transitioning: boolean;
  reversing: boolean;
  onReach: () => void;
  onSphereClick: () => void;
  distortion?: number;
}) {

  const meshRef = useRef<Mesh>(null!);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const materialRef = useRef<any>(null!);
  const groupRef = useRef<Group>(null!);

  useFrame(() => {
    // rotation
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.002;
    }
    // ambient distortion pulse
    if (materialRef.current) {
      const base = distortion ?? 0.15;
      const spike = distortion ? distortion + 0.1 : 0.25;
      const targetDistort = tapped ? spike : base;
      materialRef.current.distort += (targetDistort - materialRef.current.distort) * 0.075;
    }
    // transition scale-up
    if (transitioning && groupRef.current) {
      groupRef.current.scale.lerp(new Vector3(20, 20, 20), 0.07);
      if (groupRef.current.scale.x > 19.9) onReach();
    }
    // reverse transition scale-down
    if (reversing && groupRef.current) {
      groupRef.current.scale.lerp(new Vector3(1, 1, 1), 0.07);
      if (groupRef.current.scale.x < 1.05) {
        onReach();
      }
    }
  });

  return (
    <group ref={groupRef} scale={[1, 1, 1]}>
      <Sphere ref={meshRef} args={[1.7, 64, 64]} onPointerDown={(e) => { e.stopPropagation(); onSphereClick(); }}>
        <MeshDistortMaterial
          ref={materialRef}
          color="#FFD700"
          distort={distortion ?? 0.15}        // base ambient distortion
          speed={1.5}
          roughness={0.2}
        />
      </Sphere>
    </group>
  );
}

export default function Orb({
  triggerTransition = false,
  triggerReverse = false,
  distortion,
}: {
  triggerTransition?: boolean;
  triggerReverse?: boolean;
  distortion?: number;
}) {
  const [tapped, setTapped] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [reversing, setReversing] = useState(false);
  const router = useRouter();
  const navigated = useRef(false);

  const handleTap = () => {
    setTapped(true);
    if (triggerTransition) setTransitioning(true);
    else setTimeout(() => setTapped(false), 500);
  };

  const handleReach = () => {
    if (!navigated.current) {
      navigated.current = true;
      if (reversing) {
        router.push('/');
      } else {
        router.push('/journal');
      }
    }
  };

  useEffect(() => {
    if (triggerReverse) {
      setReversing(true);
    }
  }, [triggerReverse]);

const containerStyle: CSSProperties = {
  padding: '0vh',
  boxSizing: 'border-box',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  touchAction: 'manipulation',
  width: '100vw',
  height: '100vh',
  overflow: 'hidden',
  position: transitioning || reversing ? 'fixed' : 'relative',
  top: 0,
  left: 0,
  zIndex: transitioning || reversing ? 999 : undefined,
  backgroundColor: transitioning || reversing ? '#F9E66B' : undefined,
};
const canvasStyle: CSSProperties = {
  width: '80vmin',
  height: '80vmin',
  maxWidth: '90vw',
  maxHeight: '90vh',
};
  return (
    <div
      onClick={() => {
        setTapped(true);
        setTimeout(() => setTapped(false), 500);
      }}
      style={containerStyle}
    >
      <Canvas style={canvasStyle} camera={{ position: [0, 0, 3] }}>
        <ambientLight intensity={1.5} />
        <directionalLight intensity={4.0} position={[4, 7, 7]} />
        <Suspense fallback={null}>
          <AnimatedOrb
            tapped={tapped}
            transitioning={transitioning}
            reversing={reversing}
            distortion={distortion}
            onReach={handleReach}
            onSphereClick={handleTap}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
