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
  // Size configurations - matched so GEO and Tutor align at baseline
  // The logo height is set to match the text cap-height proportionally
  const sizeConfig = {
    sm: { logoHeight: "h-5", fontSize: "text-base", gap: "gap-0.5" },
    md: { logoHeight: "h-7", fontSize: "text-xl", gap: "gap-0.5" },
    lg: { logoHeight: "h-9", fontSize: "text-2xl", gap: "gap-1" },
  };

  const { logoHeight, fontSize, gap } = sizeConfig[size];

  return (
    <div className={`flex items-end ${gap} ${className}`}>
      {/* GEO logo image - baseline aligned with text */}
      <img
        src="/geotutor-logo.png"
        alt="GEO"
        className={`${logoHeight} w-auto object-contain`}
        style={{ marginBottom: "0.1em" }}  // Fine-tune baseline alignment
      />
      {/* Tutor text */}
      {showText && (
        <span className={`font-bold text-gray-900 ${fontSize} tracking-tight leading-none`}>
          Tutor
        </span>
      )}
    </div>
  );
}
