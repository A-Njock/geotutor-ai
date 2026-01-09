interface GeoTutorLogoProps {
  className?: string;
  showText?: boolean;
  size?: "sm" | "md" | "lg";
}

/**
 * GeoTutor logo component with the stylized "GEO" imagery
 * and optional "Tutor" text.
 */
export function GeoTutorLogo({
  className = "",
  showText = true,
  size = "md",
}: GeoTutorLogoProps) {
  // Size configurations
  const sizeConfig = {
    sm: { logoHeight: "h-6", fontSize: "text-lg", gap: "gap-0" },
    md: { logoHeight: "h-8", fontSize: "text-xl", gap: "gap-0.5" },
    lg: { logoHeight: "h-10", fontSize: "text-2xl", gap: "gap-1" },
  };

  const { logoHeight, fontSize, gap } = sizeConfig[size];

  return (
    <div className={`flex items-center ${gap} ${className}`}>
      {/* GEO logo image */}
      <img
        src="/geotutor-logo.png"
        alt="GEO"
        className={`${logoHeight} w-auto object-contain`}
      />
      {/* Tutor text */}
      {showText && (
        <span className={`font-bold text-gray-900 ${fontSize} tracking-tight`}>
          Tutor
        </span>
      )}
    </div>
  );
}
