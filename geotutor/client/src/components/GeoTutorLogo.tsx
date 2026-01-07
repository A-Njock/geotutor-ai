export function GeoTutorLogo({ className = "w-8 h-8" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Back layer - Light Blue */}
      <rect x="8" y="8" width="48" height="48" rx="8" fill="#E0F2FE" opacity="0.8" />
      
      {/* Middle layer - Medium Blue */}
      <rect x="12" y="12" width="40" height="40" rx="6" fill="#0EA5E9" opacity="0.6" />
      
      {/* Front layer - Dark Blue */}
      <rect x="16" y="16" width="32" height="32" rx="4" fill="#0369A1" />
    </svg>
  );
}
