import type { ApexOptions } from 'apexcharts'

/**
 * One ApexCharts theme for the whole console, so the log volume chart and the
 * candlestick charts that land later cannot drift apart. Apex renders into an
 * SVG that never sees our Tailwind classes, so the tokens from main.css are
 * repeated here as literals — change both or the charts stop matching the shell.
 */
export const chartInk = {
  surface: '#14120E',
  line: '#241F16',
  text: '#8A8271',
  textStrong: '#E0D9C8',
  gold: '#D4AF37',
  goldLight: '#F7C24D',
  up: '#5FB84F',
  down: '#E0524A',
} as const

/**
 * Log levels are a *status* palette, not a categorical one: debug and info stay
 * deliberately neutral so warning and error are the only things that carry hue.
 * The pairs clear CVD ΔE 11.8 and normal-vision ΔE 15.9 against the chart
 * surface, and every chip carries its label, so colour is never the only cue.
 * Critical shares error's red and separates on fill weight instead.
 */
export const levelInk = {
  debug: '#8A8271',
  info: '#E0D9C8',
  warning: '#E8952F',
  error: '#E0524A',
  critical: '#E0524A',
} as const

const fontMono = "ui-monospace, SFMono-Regular, 'JetBrains Mono', Menlo, Consolas, monospace"

/** The shared spine: chrome, grid, axes, tooltip. Merge a series spec onto it. */
export function baseChartOptions(): ApexOptions {
  return {
    chart: {
      background: 'transparent',
      foreColor: chartInk.text,
      fontFamily: fontMono,
      toolbar: { show: false },
      zoom: { enabled: false },
      animations: { enabled: true, speed: 320 },
      parentHeightOffset: 0,
    },
    theme: { mode: 'dark' },
    grid: {
      borderColor: chartInk.line,
      strokeDashArray: 3,
      xaxis: { lines: { show: false } },
      yaxis: { lines: { show: true } },
      padding: { top: 0, right: 8, bottom: 0, left: 4 },
    },
    dataLabels: { enabled: false },
    xaxis: {
      axisBorder: { color: chartInk.line },
      axisTicks: { color: chartInk.line },
      labels: { style: { fontSize: '9px', colors: chartInk.text } },
      crosshairs: { stroke: { color: chartInk.line, width: 1, dashArray: 3 } },
      tooltip: { enabled: false },
    },
    yaxis: {
      labels: { style: { fontSize: '9px', colors: chartInk.text } },
    },
    tooltip: {
      theme: 'dark',
      style: { fontSize: '11px', fontFamily: fontMono },
      x: { show: true },
    },
    legend: {
      labels: { colors: chartInk.text },
      fontSize: '10px',
      markers: { size: 5 },
      itemMargin: { horizontal: 8 },
    },
    noData: {
      text: 'No data in this range',
      style: { color: chartInk.text, fontSize: '11px', fontFamily: fontMono },
    },
  }
}
