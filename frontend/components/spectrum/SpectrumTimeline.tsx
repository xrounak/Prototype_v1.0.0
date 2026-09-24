'use client';

import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Radio,
  Scan,
  Activity,
  Layers,
  Sparkles,
} from 'lucide-react';
import {
  EmissionEvent,
  EmitterConfig,
  ScanWindow,
  Observation,
} from '../../lib/types';

interface SpectrumTimelineProps {
  simulationTime: number;
  simulationState: string;
  emitters: EmitterConfig[];
  emissionEvents: EmissionEvent[];
  scanWindows: ScanWindow[];
  lastObservation: Observation | null;
}

// Visual color palette based on behavior pattern
const BEHAVIOR_COLORS: Record<string, { fill: string; stroke: string; glow: string }> = {
  CONTINUOUS: {
    fill: 'rgba(168, 85, 247, 0.45)',
    stroke: '#c084fc',
    glow: 'rgba(168, 85, 247, 0.7)',
  },
  PERIODIC: {
    fill: 'rgba(245, 158, 11, 0.5)',
    stroke: '#fbbf24',
    glow: 'rgba(245, 158, 11, 0.7)',
  },
  BURST: {
    fill: 'rgba(6, 182, 212, 0.5)',
    stroke: '#22d3ee',
    glow: 'rgba(6, 182, 212, 0.7)',
  },
  JITTERED: {
    fill: 'rgba(234, 179, 8, 0.5)',
    stroke: '#fde047',
    glow: 'rgba(234, 179, 8, 0.7)',
  },
  STAGGERED: {
    fill: 'rgba(59, 130, 246, 0.5)',
    stroke: '#60a5fa',
    glow: 'rgba(59, 130, 246, 0.7)',
  },
  FREQUENCY_HOPPING: {
    fill: 'rgba(16, 185, 129, 0.55)',
    stroke: '#34d399',
    glow: 'rgba(16, 185, 129, 0.7)',
  },
  FREQUENCY_AGILE: {
    fill: 'rgba(244, 63, 94, 0.55)',
    stroke: '#fb7185',
    glow: 'rgba(244, 63, 94, 0.7)',
  },
};

const DEFAULT_COLOR = {
  fill: 'rgba(56, 189, 248, 0.45)',
  stroke: '#38bdf8',
  glow: 'rgba(56, 189, 248, 0.7)',
};

interface HoverInfo {
  type: 'EMISSION' | 'SCAN';
  x: number;
  y: number;
  data: any;
}

export const SpectrumTimeline: React.FC<SpectrumTimelineProps> = ({
  simulationTime,
  simulationState,
  emitters,
  emissionEvents,
  scanWindows,
  lastObservation,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Frequency Zoom / Pan state - initial default covers wide radar spectrum
  const [freqMinHz, setFreqMinHz] = useState<number>(300_000_000);    // 300 MHz
  const [freqMaxHz, setFreqMaxHz] = useState<number>(10_000_000_000); // 10 GHz
  const [timeWindowSec, setTimeWindowSec] = useState<number>(5.0);    // 5s viewport

  // Hover detection state
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null);

  // Emitter map by ID for fast name lookup
  const emitterMap = useMemo(() => {
    const map = new Map<string, EmitterConfig>();
    for (const em of emitters) {
      map.set(em.emitter_id, em);
    }
    return map;
  }, [emitters]);

  // Dynamically adapt frequency scale when emitter population changes (e.g. environment switch)
  useEffect(() => {
    if (emitters && emitters.length > 0) {
      let minF = Infinity;
      let maxF = -Infinity;
      for (const em of emitters) {
        const f = em.rf?.center_frequency_hz ?? em.frequency_hz ?? 1e9;
        const bw = em.rf?.bandwidth_hz ?? em.bandwidth_hz ?? 20e6;
        minF = Math.min(minF, f - bw * 2);
        maxF = Math.max(maxF, f + bw * 2);
      }
      if (minF !== Infinity && maxF !== -Infinity && maxF > minF) {
        const span = maxF - minF;
        const pad = Math.max(100e6, span * 0.1);
        const newMin = Math.max(100e6, Math.floor((minF - pad) / 1e8) * 1e8);
        const newMax = Math.ceil((maxF + pad) / 1e8) * 1e8;
        setFreqMinHz(newMin);
        setFreqMaxHz(newMax);
      }
    }
  }, [emitters]);

  const handleZoom = (factor: number) => {
    const center = (freqMinHz + freqMaxHz) / 2;
    const currentSpan = freqMaxHz - freqMinHz;
    const newSpan = Math.max(100_000_000, Math.min(22_000_000_000, currentSpan * factor));
    setFreqMinHz(Math.max(50_000_000, center - newSpan / 2));
    setFreqMaxHz(center + newSpan / 2);
  };

  const handlePresetSpan = (minF: number, maxF: number) => {
    setFreqMinHz(minF);
    setFreqMaxHz(maxF);
  };

  const handleAutoFitScenario = () => {
    if (emitters && emitters.length > 0) {
      let minF = Infinity;
      let maxF = -Infinity;
      for (const em of emitters) {
        const f = em.rf?.center_frequency_hz ?? em.frequency_hz ?? 1e9;
        const bw = em.rf?.bandwidth_hz ?? em.bandwidth_hz ?? 20e6;
        minF = Math.min(minF, f - bw * 2);
        maxF = Math.max(maxF, f + bw * 2);
      }
      const span = maxF - minF;
      const pad = Math.max(100e6, span * 0.1);
      setFreqMinHz(Math.max(100e6, Math.floor((minF - pad) / 1e8) * 1e8));
      setFreqMaxHz(Math.ceil((maxF + pad) / 1e8) * 1e8);
    } else {
      setFreqMinHz(300_000_000);
      setFreqMaxHz(4_000_000_000);
    }
  };

  // Convert Frequency (Hz) -> X (pixels)
  // Perfectly linear mapping across [freqMinHz, freqMaxHz]
  const freqToX = useCallback(
    (freqHz: number, plotLeft: number, plotWidth: number) => {
      const span = freqMaxHz - freqMinHz;
      if (span <= 0) return plotLeft;
      return plotLeft + ((freqHz - freqMinHz) / span) * plotWidth;
    },
    [freqMinHz, freqMaxHz]
  );

  // Convert Time (seconds) -> Y (pixels)
  // Y = Simulation Time (0 is at the bottom, progressing upwards!)
  const timeToY = useCallback(
    (timeSec: number, viewMinTime: number, viewMaxTime: number, plotTop: number, plotHeight: number) => {
      const timeSpan = viewMaxTime - viewMinTime;
      if (timeSpan <= 0) return plotTop + plotHeight;
      const norm = (timeSec - viewMinTime) / timeSpan;
      return plotTop + plotHeight - norm * plotHeight;
    },
    []
  );

  // Main Canvas Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // High DPI Support
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // Margins for axes
    const leftMargin = 68;
    const rightMargin = 20;
    const topMargin = 34; // Generous margin for top frequency labels
    const bottomMargin = 38;

    const plotLeft = leftMargin;
    const plotTop = topMargin;
    const plotWidth = width - leftMargin - rightMargin;
    const plotHeight = height - topMargin - bottomMargin;

    // Viewport Time calculation: Always follow live simulation clock
    const anchorTime = simulationTime;

    // Viewport Time calculation: Position NOW line at 30% from the top (70% past history below)
    const viewMaxTime = anchorTime + timeWindowSec * 0.30;
    const viewMinTime = anchorTime - timeWindowSec * 0.70;

    // 1. Clear background
    ctx.fillStyle = '#050811';
    ctx.fillRect(0, 0, width, height);

    // 2. Draw Plot Area Background
    const bgGrad = ctx.createLinearGradient(0, plotTop, 0, plotTop + plotHeight);
    bgGrad.addColorStop(0, 'rgba(8, 14, 28, 0.95)');
    bgGrad.addColorStop(1, 'rgba(2, 6, 18, 0.98)');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(plotLeft, plotTop, plotWidth, plotHeight);

    // 3. Grid Lines & Frequency Ticks (X Axis)
    const freqSpan = freqMaxHz - freqMinHz;
    let freqStep = 500_000_000;
    if (freqSpan <= 600_000_000) freqStep = 50_000_000;
    else if (freqSpan <= 1_200_000_000) freqStep = 100_000_000;
    else if (freqSpan <= 2_500_000_000) freqStep = 250_000_000;
    else if (freqSpan <= 6_000_000_000) freqStep = 500_000_000;
    else if (freqSpan <= 12_000_000_000) freqStep = 1_000_000_000;
    else freqStep = 2_000_000_000;

    const firstTick = Math.ceil(freqMinHz / freqStep) * freqStep;
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.09)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 4]);

    for (let f = firstTick; f <= freqMaxHz; f += freqStep) {
      const x = freqToX(f, plotLeft, plotWidth);
      if (x < plotLeft + 1 || x > plotLeft + plotWidth - 1) continue;

      ctx.beginPath();
      ctx.moveTo(x, plotTop);
      ctx.lineTo(x, plotTop + plotHeight);
      ctx.stroke();

      const fLabel =
        f >= 1e9
          ? `${(f / 1e9).toFixed(f % 1e9 === 0 ? 0 : 1)} GHz`
          : `${(f / 1e6).toFixed(0)} MHz`;

      // Frequency tick & label on top line
      ctx.beginPath();
      ctx.moveTo(x, plotTop);
      ctx.lineTo(x, plotTop - 5);
      ctx.stroke();

      ctx.fillStyle = '#cbd5e1';
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(fLabel, x, plotTop - 8);

      // Frequency label below
      ctx.fillStyle = '#64748b';
      ctx.font = '10px monospace';
      ctx.fillText(fLabel, x, plotTop + plotHeight + 18);
    }

    // 4. Time Ticks (Y Axis) - 0 at bottom, increasing upwards
    const timeStep = timeWindowSec <= 4 ? 0.5 : timeWindowSec <= 8 ? 1.0 : timeWindowSec <= 15 ? 2.0 : 5.0;
    const firstTimeTick = Math.ceil(viewMinTime / timeStep) * timeStep;

    for (let t = firstTimeTick; t <= viewMaxTime; t += timeStep) {
      if (t < 0) continue;
      const y = timeToY(t, viewMinTime, viewMaxTime, plotTop, plotHeight);
      if (y >= plotTop && y <= plotTop + plotHeight) {
        ctx.beginPath();
        ctx.moveTo(plotLeft, y);
        ctx.lineTo(plotLeft + plotWidth, y);
        ctx.stroke();

        // Time label on left
        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`${t.toFixed(1)}s`, plotLeft - 8, y + 3);
      }
    }
    ctx.setLineDash([]); // Reset dashed line

    // 5. Render EMISSION_EVENT Rectangles
    // Symmetrically centered on true RF center frequency to eliminate X misalignment!
    for (const ev of emissionEvents) {
      // CAUSAL GUARD: Strictly ignore events from future or previous run before reset
      if (ev.timestamp > simulationTime + 0.02) continue;
      // Cull events out of time or frequency viewport
      if (ev.time_end < viewMinTime || ev.timestamp > viewMaxTime) continue;
      if (ev.frequency_end_hz < freqMinHz || ev.frequency_start_hz > freqMaxHz) continue;

      const centerF = (ev.frequency_start_hz + ev.frequency_end_hz) / 2.0;
      const xCenter = freqToX(centerF, plotLeft, plotWidth);
      const xStart = freqToX(ev.frequency_start_hz, plotLeft, plotWidth);
      const xEnd = freqToX(ev.frequency_end_hz, plotLeft, plotWidth);

      // Clamp pulse top to current simulation time so pulses grow upwards live
      const effectiveEnd = Math.min(ev.time_end, simulationTime + 0.02);
      const yBottom = timeToY(ev.timestamp, viewMinTime, viewMaxTime, plotTop, plotHeight);
      const yTop = timeToY(effectiveEnd, viewMinTime, viewMaxTime, plotTop, plotHeight);

      // Width calculation: maintain minimum 6px for visibility, but centered on xCenter
      const rawWidth = Math.abs(xEnd - xStart);
      const rectWidth = Math.max(6, rawWidth);
      const rectX = Math.max(plotLeft, Math.min(plotLeft + plotWidth - rectWidth, xCenter - rectWidth / 2));

      const rectHeight = Math.max(3, yBottom - yTop);
      const rectY = yTop;

      const style = BEHAVIOR_COLORS[ev.behavior] || DEFAULT_COLOR;

      // Fill emission bar
      ctx.fillStyle = style.fill;
      ctx.fillRect(rectX, rectY, rectWidth, rectHeight);

      // Stroke border
      ctx.strokeStyle = style.stroke;
      ctx.lineWidth = 1.3;
      ctx.strokeRect(rectX, rectY, rectWidth, rectHeight);

      // Pulse emitter ID label if rectangle has sufficient height and width
      if (rectHeight >= 12 && rectWidth >= 30) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(ev.emitter_id, rectX + rectWidth / 2, rectY + rectHeight / 2 + 3);
      }
    }

    // 6. Render RECEIVER SCAN OVERLAY Rectangles
    const recentScans = scanWindows.slice(-200);
    for (const scan of recentScans) {
      if (scan.time_start > simulationTime + 0.02) continue;
      if (scan.time_end < viewMinTime || scan.time_start > viewMaxTime) continue;
      if (scan.frequency_end_hz < freqMinHz || scan.frequency_start_hz > freqMaxHz) continue;

      const sxStart = freqToX(scan.frequency_start_hz, plotLeft, plotWidth);
      const sxEnd = freqToX(scan.frequency_end_hz, plotLeft, plotWidth);
      const effectiveScanEnd = Math.min(scan.time_end, simulationTime + 0.02);
      const syBottom = timeToY(scan.time_start, viewMinTime, viewMaxTime, plotTop, plotHeight);
      const syTop = timeToY(effectiveScanEnd, viewMinTime, viewMaxTime, plotTop, plotHeight);

      const drawStartX = Math.max(plotLeft, sxStart);
      const drawEndX = Math.min(plotLeft + plotWidth, sxEnd);
      const sWidth = Math.max(4, drawEndX - drawStartX);
      const sHeight = Math.max(3, syBottom - syTop);

      // Check if this scan is currently active (touching or close to simulationTime)
      const isCurrent = Math.abs(effectiveScanEnd - simulationTime) < 0.12;

      // Clean glowing scan overlay
      ctx.fillStyle = isCurrent ? 'rgba(0, 240, 255, 0.20)' : 'rgba(0, 240, 255, 0.08)';
      ctx.fillRect(drawStartX, syTop, sWidth, sHeight);

      // Distinctive glowing border
      ctx.strokeStyle = isCurrent ? '#00f0ff' : 'rgba(0, 240, 255, 0.45)';
      ctx.lineWidth = isCurrent ? 1.8 : 1.0;
      ctx.strokeRect(drawStartX, syTop, sWidth, sHeight);

      // Sleek corner reticle accents
      if (isCurrent || sHeight >= 8) {
        const markerLen = Math.min(6, sWidth / 4);
        ctx.strokeStyle = isCurrent ? '#ffffff' : 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        // Top-left
        ctx.moveTo(drawStartX, syTop + markerLen);
        ctx.lineTo(drawStartX, syTop);
        ctx.lineTo(drawStartX + markerLen, syTop);
        // Top-right
        ctx.moveTo(drawEndX - markerLen, syTop);
        ctx.lineTo(drawEndX, syTop);
        ctx.lineTo(drawEndX, syTop + markerLen);
        ctx.stroke();
      }

      // Scan Tag on active scan
      if (sWidth >= 55 && (isCurrent || sHeight >= 12)) {
        ctx.fillStyle = isCurrent ? '#00f0ff' : 'rgba(0, 240, 255, 0.7)';
        ctx.font = 'bold 8.5px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(
          `RX ${((scan.frequency_end_hz - scan.frequency_start_hz) / 1e6).toFixed(0)}M`,
          drawStartX + 4,
          syTop + Math.min(10, sHeight / 2 + 3)
        );
      }
    }

    // 7. Render Current Simulation Time Indicator Line & Future Zone Dimming
    const curY = timeToY(simulationTime, viewMinTime, viewMaxTime, plotTop, plotHeight);

    // Dim unelapsed future time zone above the current time line
    if (curY > plotTop && curY <= plotTop + plotHeight) {
      ctx.fillStyle = 'rgba(3, 7, 18, 0.35)';
      ctx.fillRect(plotLeft, plotTop, plotWidth, curY - plotTop);

      // Subtle diagonal warning hatch in future area
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.04)';
      ctx.lineWidth = 1;
      const hatchSpacing = 24;
      ctx.save();
      ctx.beginPath();
      ctx.rect(plotLeft, plotTop, plotWidth, curY - plotTop);
      ctx.clip();
      for (let x = plotLeft - (curY - plotTop); x < plotLeft + plotWidth + hatchSpacing; x += hatchSpacing) {
        ctx.moveTo(x, plotTop);
        ctx.lineTo(x + (curY - plotTop), curY);
      }
      ctx.stroke();
      ctx.restore();
    }

    if (curY >= plotTop && curY <= plotTop + plotHeight) {
      // Vivid Neon Cyan Glow Line
      ctx.save();
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 2.0;
      ctx.shadowColor = '#00f0ff';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.moveTo(plotLeft, curY);
      ctx.lineTo(plotLeft + plotWidth, curY);
      ctx.stroke();
      ctx.restore();

      // "NOW" badge on left margin
      ctx.fillStyle = '#00f0ff';
      ctx.fillRect(plotLeft - 54, curY - 8, 50, 16);
      ctx.fillStyle = '#020617';
      ctx.font = 'bold 9px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`${simulationTime.toFixed(2)}s`, plotLeft - 29, curY + 4);
    }

    // 8. Outer Axis Borders
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(plotLeft, plotTop, plotWidth, plotHeight);

    // 9. Axis Titles
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('FREQUENCY (Hz) →', plotLeft + plotWidth / 2, height - 8);

    ctx.save();
    ctx.translate(14, plotTop + plotHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('SIMULATION TIME (s) ↑', 0, 0);
    ctx.restore();
  }, [
    freqMinHz,
    freqMaxHz,
    timeWindowSec,
    simulationTime,
    emissionEvents,
    scanWindows,
    freqToX,
    timeToY,
  ]);

  // Handle Canvas Mouse Move for Hover Tooltips
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const leftMargin = 68;
    const rightMargin = 20;
    const topMargin = 34;
    const bottomMargin = 38;
    const plotLeft = leftMargin;
    const plotTop = topMargin;
    const plotWidth = rect.width - leftMargin - rightMargin;
    const plotHeight = rect.height - topMargin - bottomMargin;

    if (
      mouseX < plotLeft ||
      mouseX > plotLeft + plotWidth ||
      mouseY < plotTop ||
      mouseY > plotTop + plotHeight
    ) {
      setHoverInfo(null);
      return;
    }

    const anchorTime = simulationTime;

    const viewMaxTime = anchorTime + timeWindowSec * 0.30;
    const viewMinTime = anchorTime - timeWindowSec * 0.70;

    // Check Receiver Scan hit
    for (const scan of scanWindows.slice(-200)) {
      if (scan.frequency_end_hz < freqMinHz || scan.frequency_start_hz > freqMaxHz) continue;
      const sxStart = freqToX(scan.frequency_start_hz, plotLeft, plotWidth);
      const sxEnd = freqToX(scan.frequency_end_hz, plotLeft, plotWidth);
      const syBottom = timeToY(scan.time_start, viewMinTime, viewMaxTime, plotTop, plotHeight);
      const syTop = timeToY(scan.time_end, viewMinTime, viewMaxTime, plotTop, plotHeight);

      if (
        mouseX >= sxStart &&
        mouseX <= sxEnd &&
        mouseY >= syTop &&
        mouseY <= syBottom
      ) {
        setHoverInfo({
          type: 'SCAN',
          x: e.clientX,
          y: e.clientY,
          data: scan,
        });
        return;
      }
    }

    // Check Emission Events hit (symmetrically centered)
    for (let i = emissionEvents.length - 1; i >= 0; i--) {
      const ev = emissionEvents[i];
      if (ev.frequency_end_hz < freqMinHz || ev.frequency_start_hz > freqMaxHz) continue;
      if (ev.time_end < viewMinTime || ev.timestamp > viewMaxTime) continue;

      const centerF = (ev.frequency_start_hz + ev.frequency_end_hz) / 2.0;
      const xCenter = freqToX(centerF, plotLeft, plotWidth);
      const xStart = freqToX(ev.frequency_start_hz, plotLeft, plotWidth);
      const xEnd = freqToX(ev.frequency_end_hz, plotLeft, plotWidth);
      const rawWidth = Math.abs(xEnd - xStart);
      const rectWidth = Math.max(8, rawWidth);
      const rectX = xCenter - rectWidth / 2;

      const yBottom = timeToY(ev.timestamp, viewMinTime, viewMaxTime, plotTop, plotHeight);
      const yTop = timeToY(ev.time_end, viewMinTime, viewMaxTime, plotTop, plotHeight);

      if (
        mouseX >= rectX - 2 &&
        mouseX <= rectX + rectWidth + 2 &&
        mouseY >= yTop - 2 &&
        mouseY <= yBottom + 2
      ) {
        const emProfile = emitterMap.get(ev.emitter_id);
        setHoverInfo({
          type: 'EMISSION',
          x: e.clientX,
          y: e.clientY,
          data: {
            ...ev,
            emitter_name: emProfile?.name || ev.emitter_id,
          },
        });
        return;
      }
    }

    setHoverInfo(null);
  };

  const handleMouseLeave = () => {
    setHoverInfo(null);
  };

  return (
    <div
      ref={containerRef}
      className="glass-panel"
      style={{
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      {/* Top Header & Interactive Visual Controls */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#00f0ff" />
            <h2
              style={{
                fontSize: '0.95rem',
                fontWeight: 700,
                color: '#f8fafc',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              REAL-TIME ELECTROMAGNETIC SPECTRUM &amp; TIME TIMELINE
            </h2>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            X = Frequency &bull; Y = Simulation Time (s, upward) &bull; Synchronized Live Emitter &amp; Receiver Sweep
          </p>
        </div>

        {/* Viewport & Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {/* Quick Frequency Range Presets */}
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(15, 23, 42, 0.7)', borderRadius: '6px', border: '1px solid var(--border-subtle)', padding: '2px' }}>
            <button
              onClick={handleAutoFitScenario}
              style={{
                background: 'transparent',
                color: '#38bdf8',
                border: 'none',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
                fontWeight: 600,
              }}
              title="Automatically fit frequency span to all emitters in scenario"
            >
              Auto Fit
            </button>
            <button
              onClick={() => handlePresetSpan(300e6, 3.5e9)}
              style={{
                background: freqMinHz === 300e6 && freqMaxHz === 3.5e9 ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
                color: freqMinHz === 300e6 && freqMaxHz === 3.5e9 ? '#38bdf8' : '#94a3b8',
                border: 'none',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              0.3-3.5G
            </button>
            <button
              onClick={() => handlePresetSpan(300e6, 18e9)}
              style={{
                background: freqMinHz === 300e6 && freqMaxHz === 18e9 ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
                color: freqMinHz === 300e6 && freqMaxHz === 18e9 ? '#38bdf8' : '#94a3b8',
                border: 'none',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              Wide (18G)
            </button>
          </div>

          {/* Time window selector */}
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(15, 23, 42, 0.7)', borderRadius: '6px', border: '1px solid var(--border-subtle)', padding: '2px' }}>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', padding: '0 6px', fontFamily: 'var(--font-mono)' }}>Span:</span>
            {[3, 5, 10, 20].map((sec) => (
              <button
                key={sec}
                onClick={() => setTimeWindowSec(sec)}
                style={{
                  background: timeWindowSec === sec ? 'rgba(56, 189, 248, 0.25)' : 'transparent',
                  color: timeWindowSec === sec ? '#38bdf8' : '#94a3b8',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  fontSize: '0.72rem',
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer',
                  fontWeight: timeWindowSec === sec ? 700 : 500,
                }}
              >
                {sec}s
              </button>
            ))}
          </div>

          {/* Frequency Zoom buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <button
              onClick={() => handleZoom(0.7)}
              className="btn btn-secondary"
              style={{ padding: '5px 8px' }}
              title="Zoom in frequency (X-axis)"
            >
              <ZoomIn size={14} />
            </button>
            <button
              onClick={() => handleZoom(1.4)}
              className="btn btn-secondary"
              style={{ padding: '5px 8px' }}
              title="Zoom out frequency (X-axis)"
            >
              <ZoomOut size={14} />
            </button>
            <button
              onClick={handleAutoFitScenario}
              className="btn btn-secondary"
              style={{ padding: '5px 8px' }}
              title="Reset frequency view to scenario bounds"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Interactive Canvas Area */}
      <div style={{ position: 'relative', width: '100%', height: '460px', overflow: 'hidden', borderRadius: '8px' }}>
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{
            width: '100%',
            height: '100%',
            display: 'block',
            cursor: hoverInfo ? 'crosshair' : 'default',
          }}
        />

        {/* Hover Tooltip Card */}
        {hoverInfo && (
          <div
            style={{
              position: 'fixed',
              left: `${Math.min(window.innerWidth - 320, hoverInfo.x + 14)}px`,
              top: `${Math.min(window.innerHeight - 240, hoverInfo.y - 10)}px`,
              background: 'rgba(8, 12, 22, 0.96)',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              borderRadius: '8px',
              padding: '12px 14px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(16px)',
              pointerEvents: 'none',
              zIndex: 1000,
              minWidth: '270px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.72rem',
              color: '#e2e8f0',
            }}
          >
            {hoverInfo.type === 'EMISSION' ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                  <span style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.82rem' }}>
                    {hoverInfo.data.emitter_id}
                  </span>
                  <span
                    style={{
                      background: 'rgba(56, 189, 248, 0.15)',
                      padding: '1px 6px',
                      borderRadius: '3px',
                      color: '#7dd3fc',
                      fontSize: '0.65rem',
                    }}
                  >
                    {hoverInfo.data.behavior}
                  </span>
                </div>
                <div style={{ color: '#cbd5e1', fontWeight: 600 }}>{hoverInfo.data.emitter_name}</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '2px' }}>
                  <div>Category: <span style={{ color: '#fff' }}>{hoverInfo.data.emitter_category || 'RADAR'}</span></div>
                  <div>Subtype: <span style={{ color: '#fff' }}>{hoverInfo.data.emitter_subtype || 'SEARCH'}</span></div>
                  <div>Center: <span style={{ color: '#38bdf8' }}>{((hoverInfo.data.frequency_start_hz + hoverInfo.data.frequency_end_hz) / 2e6).toFixed(1)} MHz</span></div>
                  <div>BW: <span style={{ color: '#fff' }}>{((hoverInfo.data.frequency_end_hz - hoverInfo.data.frequency_start_hz) / 1e6).toFixed(1)} MHz</span></div>
                  <div>Power: <span style={{ color: '#f59e0b' }}>{hoverInfo.data.power_dbm} dBm</span></div>
                  <div>Duration: <span style={{ color: '#fff' }}>{hoverInfo.data.duration_us} &micro;s</span></div>
                  <div>Start: <span style={{ color: '#94a3b8' }}>{hoverInfo.data.timestamp.toFixed(3)}s</span></div>
                  <div>End: <span style={{ color: '#94a3b8' }}>{hoverInfo.data.time_end.toFixed(3)}s</span></div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '6px' }}>
                  <span style={{ fontWeight: 700, color: '#00f0ff', fontSize: '0.82rem' }}>
                    RECEIVER SCAN WINDOW
                  </span>
                  <span style={{ color: '#34d399', fontSize: '0.65rem' }}>{hoverInfo.data.dwell_time_ms} ms</span>
                </div>
                <div>Action ID: <span style={{ color: '#fff' }}>{hoverInfo.data.action_id || 'SWEEP'}</span></div>
                <div>Start Freq: <span style={{ color: '#38bdf8' }}>{(hoverInfo.data.frequency_start_hz / 1e6).toFixed(1)} MHz</span></div>
                <div>End Freq: <span style={{ color: '#38bdf8' }}>{(hoverInfo.data.frequency_end_hz / 1e6).toFixed(1)} MHz</span></div>
                <div>Instantaneous BW: <span style={{ color: '#fff' }}>{((hoverInfo.data.frequency_end_hz - hoverInfo.data.frequency_start_hz) / 1e6).toFixed(0)} MHz</span></div>
                <div>Time Start: <span style={{ color: '#94a3b8' }}>{hoverInfo.data.time_start.toFixed(3)}s</span></div>
                <div>Time End: <span style={{ color: '#94a3b8' }}>{hoverInfo.data.time_end.toFixed(3)}s</span></div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend & Behavior Indicators */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          paddingTop: '6px',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '10px', background: 'rgba(0, 240, 255, 0.2)', border: '2px solid #00f0ff', borderRadius: '2px' }} />
            Receiver Scan Window (500 MHz)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(6, 182, 212, 0.5)', border: '1px solid #22d3ee', borderRadius: '2px' }} />
            Burst
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(245, 158, 11, 0.5)', border: '1px solid #fbbf24', borderRadius: '2px' }} />
            Periodic
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(168, 85, 247, 0.5)', border: '1px solid #c084fc', borderRadius: '2px' }} />
            Continuous
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(16, 185, 129, 0.5)', border: '1px solid #34d399', borderRadius: '2px' }} />
            Frequency Hopping
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(244, 63, 94, 0.5)', border: '1px solid #fb7185', borderRadius: '2px' }} />
            Frequency Agile
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(234, 179, 8, 0.5)', border: '1px solid #fde047', borderRadius: '2px' }} />
            Jittered
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(59, 130, 246, 0.5)', border: '1px solid #60a5fa', borderRadius: '2px' }} />
            Staggered
          </span>
        </div>

        <span style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
          {emissionEvents.length} events logged &bull; Real-time synchronized stream
        </span>
      </div>
    </div>
  );
};
