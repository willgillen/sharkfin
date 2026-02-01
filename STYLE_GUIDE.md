# Shark Fin Style Guide

This document defines the visual design system for Shark Fin. All frontend components must use these semantic color tokens and patterns to maintain consistency across the application.

## Design Principles

1. **Use Semantic Colors**: Always use the semantic color tokens defined in `tailwind.config.ts` instead of raw Tailwind colors (e.g., use `text-danger-600` not `text-red-600`).
2. **Maintain Consistency**: All similar UI patterns should look identical throughout the application.
3. **Accessibility First**: Color choices meet WCAG AA contrast requirements.
4. **Predictable Hierarchy**: Use consistent text and background hierarchies.

---

## Color System

All colors are defined in `frontend/tailwind.config.ts`. The following semantic tokens are available:

### Text Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `text-text-primary` | `#111827` | Main body text, headings |
| `text-text-secondary` | `#4b5563` | Secondary/supporting text, descriptions |
| `text-text-tertiary` | `#6b7280` | Tertiary text, labels, hints |
| `text-text-disabled` | `#9ca3af` | Disabled states |
| `text-text-inverse` | `#ffffff` | Text on dark backgrounds |

**Examples:**
```tsx
<h1 className="text-text-primary">Main Heading</h1>
<p className="text-text-secondary">Description text</p>
<span className="text-text-tertiary">Helper text</span>
```

### Background Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `bg-surface` | `#ffffff` | Primary surface/cards |
| `bg-surface-secondary` | `#f9fafb` | Secondary surface, hover states |
| `bg-surface-tertiary` | `#f3f4f6` | Tertiary surface, disabled backgrounds |

**Examples:**
```tsx
<div className="bg-surface rounded-lg p-6">Card content</div>
<div className="bg-surface-secondary">Alternative background</div>
```

### Border Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `border-border` | `#d1d5db` | Default borders |
| `border-border-light` | `#e5e7eb` | Light borders, subtle dividers |
| `border-border-dark` | `#9ca3af` | Emphasized borders |

**Examples:**
```tsx
<div className="border border-border rounded-md">Default border</div>
<hr className="border-border-light" />
```

### Status Colors

Use these for feedback messages, alerts, and status indicators.

#### Success (Green)
| Token | Usage |
|-------|-------|
| `bg-success-50` | Success alert background |
| `bg-success-100` | Success badge background |
| `text-success-600` | Success text |
| `text-success-700` | Success badge text |
| `border-success-200` | Success alert border |

#### Warning (Yellow/Amber)
| Token | Usage |
|-------|-------|
| `bg-warning-50` | Warning alert background |
| `bg-warning-100` | Warning badge background |
| `text-warning-600` | Warning text, inline warnings |
| `text-warning-700` | Warning badge text |
| `border-warning-200` | Warning alert border |

#### Danger/Error (Red)
| Token | Usage |
|-------|-------|
| `bg-danger-50` | Error alert background |
| `bg-danger-100` | Error badge background |
| `text-danger-600` | Error text, inline errors |
| `text-danger-700` | Error badge text |
| `border-danger-200` | Error alert border |
| `border-danger-300` | Danger button border |

### Primary Brand Colors

| Token | Usage |
|-------|-------|
| `bg-primary-50` | Selected state background |
| `bg-primary-600` | Primary buttons |
| `bg-primary-700` | Primary button hover |
| `text-primary-600` | Links, interactive text |
| `text-primary-900` | Link hover |
| `border-primary-300` | Interactive border hover |
| `border-primary-500` | Selected/active border |
| `focus:ring-primary-500` | Focus ring |

### Transaction Colors

Use these specifically for transaction-related displays:

| Token | Usage |
|-------|-------|
| `text-expense-600` | Expense amounts (negative) |
| `bg-expense-50` | Expense highlight background |
| `text-income-600` | Income amounts (positive) |
| `bg-income-50` | Income highlight background |
| `text-transfer-600` | Transfer amounts |
| `bg-transfer-50` | Transfer highlight background |

---

## Common UI Patterns

### Alert Messages

```tsx
{/* Error Alert */}
<div className="p-3 bg-danger-50 border border-danger-200 rounded-md text-sm text-danger-600">
  Error message here
</div>

{/* Success Alert */}
<div className="p-3 bg-success-50 border border-success-200 rounded-md text-sm text-success-600">
  Success message here
</div>

{/* Warning Alert */}
<div className="p-3 bg-warning-50 border border-warning-200 rounded-md text-sm text-warning-700">
  Warning message here
</div>
```

### Status Badges

```tsx
{/* Success/Active Badge */}
<span className="text-xs px-2 py-1 bg-success-100 text-success-700 rounded-full">
  Active
</span>

{/* Warning Badge */}
<span className="text-xs px-2 py-1 bg-warning-100 text-warning-700 rounded-full">
  Pending
</span>

{/* Error Badge */}
<span className="text-xs px-2 py-1 bg-danger-100 text-danger-700 rounded-full">
  Error
</span>
```

### Buttons

```tsx
{/* Primary Button */}
<button className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed">
  Save
</button>

{/* Secondary/Outline Button */}
<button className="px-4 py-2 border border-border text-text-primary text-sm font-medium rounded-md hover:bg-surface-secondary">
  Cancel
</button>

{/* Danger Button */}
<button className="px-4 py-2 border border-danger-300 text-danger-600 text-sm font-medium rounded-md hover:bg-danger-50">
  Delete
</button>
```

### Links

```tsx
<a href="#" className="text-primary-600 hover:underline">
  Click here
</a>

{/* In text context */}
<a href="#" className="text-primary-600 hover:text-primary-900">
  Learn more
</a>
```

### Cards/Containers

```tsx
<div className="bg-surface rounded-lg p-6">
  <h3 className="text-lg font-medium text-text-primary mb-2">Title</h3>
  <p className="text-sm text-text-secondary mb-6">
    Description text
  </p>
  {/* Card content */}
</div>
```

### Form Inputs

```tsx
<input
  type="text"
  className="w-full px-3 py-2 border border-border rounded-md text-sm text-text-primary placeholder:text-text-tertiary focus:ring-primary-500 focus:border-primary-500"
  placeholder="Enter value"
/>
```

### Loading States

```tsx
{/* Skeleton loading */}
<div className="animate-pulse">
  <div className="h-6 bg-surface-secondary rounded w-1/3 mb-4"></div>
  <div className="h-4 bg-surface-secondary rounded w-2/3"></div>
</div>

{/* Spinner */}
<svg className="animate-spin h-4 w-4 text-text-secondary" fill="none" viewBox="0 0 24 24">
  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
</svg>
```

### Radio/Checkbox Selection Cards

```tsx
<label className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${
  isSelected
    ? "border-primary-500 bg-primary-50"
    : "border-border hover:border-primary-300"
}`}>
  <input
    type="radio"
    className="mt-1 h-4 w-4 text-primary-600 border-border focus:ring-primary-500"
  />
  <div className="ml-3 flex-1">
    <span className="text-sm font-medium text-text-primary">Option Title</span>
    <p className="mt-1 text-sm text-text-secondary">Description</p>
  </div>
</label>
```

---

## What NOT to Use

Never use raw Tailwind color classes. Always use the semantic tokens:

| Wrong | Correct |
|-------|---------|
| `text-red-600` | `text-danger-600` |
| `text-green-600` | `text-success-600` |
| `text-yellow-600` | `text-warning-600` |
| `text-gray-900` | `text-text-primary` |
| `text-gray-600` | `text-text-secondary` |
| `text-gray-500` | `text-text-tertiary` |
| `bg-red-50` | `bg-danger-50` |
| `bg-green-50` | `bg-success-50` |
| `bg-yellow-50` | `bg-warning-50` |
| `bg-gray-50` | `bg-surface-secondary` |
| `bg-white` | `bg-surface` |
| `border-gray-300` | `border-border` |
| `border-red-200` | `border-danger-200` |
| `border-green-200` | `border-success-200` |
| `border-yellow-200` | `border-warning-200` |

---

## Typography

### Headings

```tsx
<h1 className="text-2xl font-semibold text-text-primary">Page Title</h1>
<h2 className="text-xl font-semibold text-text-primary">Section Title</h2>
<h3 className="text-lg font-medium text-text-primary">Card Title</h3>
<h4 className="text-sm font-medium text-text-primary">Subsection Title</h4>
```

### Body Text

```tsx
<p className="text-sm text-text-primary">Primary body text</p>
<p className="text-sm text-text-secondary">Secondary/description text</p>
<p className="text-xs text-text-tertiary">Helper/meta text</p>
```

---

## Spacing Standards

- **Card padding**: `p-6`
- **Section spacing**: `space-y-8` or `mb-8`
- **Element spacing within cards**: `space-y-4` or `mb-4`
- **Button groups**: `gap-2`
- **Form element margins**: `mb-3` or `mb-4`

---

## Border Radius

- **Cards/containers**: `rounded-lg`
- **Buttons/inputs**: `rounded-md`
- **Badges/pills**: `rounded-full`

---

## Transitions

Use `transition-colors` for hover state changes on interactive elements:

```tsx
<button className="... transition-colors hover:bg-primary-700">
```

---

*Last Updated: 2026-01-31*
