// client/src/features/analytics/config/chartTheme.js

export const CHART_THEMES = {
  light: {
    gridStroke:        "#F1F5F9",
    axisTickFill:      "#94A3B8",
    axisTickFontSize:  11,

    tooltipBg:         "#FFFFFF",
    tooltipBorder:     "#E2E8F0",
    tooltipShadow:     "0 8px 24px rgba(15,23,42,0.10)",
    tooltipLabelColor: "#475569",
    tooltipValueColor: "#0F172A",

    storageStroke:     "#2563EB",
    storageGradStart:  "rgba(37,99,235,0.15)",
    storageGradEnd:    "rgba(37,99,235,0.01)",
    storageDotFill:    "#2563EB",

    uploadFill:        "#2563EB",
    downloadFill:      "#818CF8",

    successStroke:     "#2563EB",
    failedStroke:      "#EF4444",
    failedDotFill:     "#EF4444",

    progressFrom:      "#3B82F6",
    progressTo:        "#6366F1",
  },

  dark: {
    gridStroke:        "#1E293B",
    axisTickFill:      "#475569",
    axisTickFontSize:  11,

    tooltipBg:         "#111827",
    tooltipBorder:     "#334155",
    tooltipShadow:     "0 8px 24px rgba(0,0,0,0.40)",
    tooltipLabelColor: "#94A3B8",
    tooltipValueColor: "#F1F5F9",

    storageStroke:     "#3B82F6",
    storageGradStart:  "rgba(59,130,246,0.20)",
    storageGradEnd:    "rgba(59,130,246,0.00)",
    storageDotFill:    "#3B82F6",

    uploadFill:        "#3B82F6",
    downloadFill:      "#6366F1",

    successStroke:     "#3B82F6",
    failedStroke:      "#F87171",
    failedDotFill:     "#F87171",

    progressFrom:      "#3B82F6",
    progressTo:        "#6366F1",
  },
};