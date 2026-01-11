interface GeoTutorLogoProps {
  className?: string;
  showText?: boolean;
  size?: "sm" | "md" | "lg";
}

/**
 * GeoTutor logo component with the stylized "GEO" imagery
 * and optional "Tutor" text, aligned at baseline.
 */
export function GeoTutorLogo({
  className = "",
  showText = true,
  size = "md",
}: GeoTutorLogoProps) {
  // Size configurations - GEO logo sized to match Tutor text height
  const sizeConfig = {
    sm: { logoHeight: "h-4", fontSize: "text-lg", gap: "gap-1" },
    md: { logoHeight: "h-6", fontSize: "text-2xl", gap: "gap-1" },
    lg: { logoHeight: "h-9", fontSize: "text-3xl", gap: "gap-2" },
  };

  const { logoHeight, fontSize, gap } = sizeConfig[size];

  return (
    <div className={`flex items-end ${gap} ${className}`}>
      {/* GEO logo image */}
      <img
        src="/geotutor-logo.png"
        alt="GEO"
        className={`${logoHeight} w-auto object-contain`}
      />
      {/* Tutor text */}
      {showText && (
        <span className={`font-bold text-slate-100 ${fontSize} tracking-tight leading-none`}>
          Tutor
        </span>
      )}
    </div>
  );
}
