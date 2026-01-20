"use client";

import { useState, useEffect } from "react";
import Image from "next/image";

interface PayeeIconProps {
  /** The logo_url stored in the payee record */
  logoUrl: string | null | undefined;
  /** Payee name for alt text and fallback */
  name: string;
  /** Size of the icon in pixels (default: 32) */
  size?: number;
  /** Additional CSS classes */
  className?: string;
}

// Default emoji when no logo is set
const DEFAULT_EMOJI = "🏪";

/**
 * Parse a logo_url into its display format.
 * Handles: emoji:X format, brand CDN URLs, custom URLs, and null/empty.
 */
function parseLogoUrl(logoUrl: string | null | undefined): {
  type: "emoji" | "brand" | "custom" | "none";
  value: string;
} {
  if (!logoUrl) {
    return { type: "none", value: DEFAULT_EMOJI };
  }

  if (logoUrl.startsWith("emoji:")) {
    return { type: "emoji", value: logoUrl.slice(6) };
  }

  if (logoUrl.includes("cdn.simpleicons.org")) {
    return { type: "brand", value: logoUrl };
  }

  // Assume it's a custom URL
  return { type: "custom", value: logoUrl };
}

/**
 * PayeeIcon component - displays a payee's visual identity.
 *
 * Supports:
 * - Brand logos from Simple Icons CDN
 * - Emoji icons stored as "emoji:X" format
 * - Custom image URLs
 * - Default fallback emoji
 */
export function PayeeIcon({ logoUrl, name, size = 32, className = "" }: PayeeIconProps) {
  const [imageError, setImageError] = useState(false);
  const parsed = parseLogoUrl(logoUrl);

  // Reset error state when logoUrl changes
  useEffect(() => {
    setImageError(false);
  }, [logoUrl]);

  const baseStyles = `inline-flex items-center justify-center rounded-lg ${className}`;
  const sizeStyle = { width: size, height: size };

  // Emoji display
  if (parsed.type === "emoji" || parsed.type === "none" || imageError) {
    const emoji = imageError ? DEFAULT_EMOJI : parsed.value;
    const fontSize = size * 0.6; // Emoji looks good at ~60% of container

    return (
      <span
        className={`${baseStyles} bg-gray-100`}
        style={{ ...sizeStyle, fontSize }}
        role="img"
        aria-label={`${name} icon`}
      >
        {emoji}
      </span>
    );
  }

  // Brand or custom image
  return (
    <span className={`${baseStyles} bg-white overflow-hidden`} style={sizeStyle}>
      <Image
        src={parsed.value}
        alt={`${name} logo`}
        width={size}
        height={size}
        className="object-contain p-1"
        onError={() => setImageError(true)}
        unoptimized // CDN images don't need Next.js optimization
      />
    </span>
  );
}

/**
 * PayeeIconLarge - larger version for edit pages and detail views.
 */
export function PayeeIconLarge({ logoUrl, name, className = "" }: Omit<PayeeIconProps, "size">) {
  return <PayeeIcon logoUrl={logoUrl} name={name} size={64} className={className} />;
}

/**
 * PayeeIconSmall - compact version for lists and tables.
 */
export function PayeeIconSmall({ logoUrl, name, className = "" }: Omit<PayeeIconProps, "size">) {
  return <PayeeIcon logoUrl={logoUrl} name={name} size={24} className={className} />;
}

// Export the parse function for use elsewhere
export { parseLogoUrl };
