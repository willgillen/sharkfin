"use client";

interface LogoDevAttributionProps {
  className?: string;
  variant?: "inline" | "footer";
}

export default function LogoDevAttribution({
  className = "",
  variant = "inline",
}: LogoDevAttributionProps) {
  if (variant === "footer") {
    return (
      <div className={`text-xs text-text-tertiary ${className}`}>
        Logos provided by{" "}
        <a
          href="https://logo.dev"
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-600 hover:underline"
        >
          Logo.dev
        </a>
      </div>
    );
  }

  // Inline variant - small badge next to logo
  return (
    <a
      href="https://logo.dev"
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center text-[10px] text-text-tertiary hover:text-primary-600 ${className}`}
      title="Logo provided by Logo.dev"
    >
      <svg
        className="w-3 h-3 mr-0.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
        />
      </svg>
      logo.dev
    </a>
  );
}
