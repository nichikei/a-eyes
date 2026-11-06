// Canvas drawing utilities for annotation overlays

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
}

/**
 * Draw bounding boxes and labels on canvas
 */
export function drawBoundingBoxes(
  canvas: HTMLCanvasElement,
  boxes: BoundingBox[],
  options: {
    strokeColor?: string;
    fillColor?: string;
    textColor?: string;
    lineWidth?: number;
    fontSize?: number;
  } = {}
) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const {
    strokeColor = '#00ff00',
    fillColor = 'rgba(0, 255, 0, 0.1)',
    textColor = '#ffffff',
    lineWidth = 2,
    fontSize = 14,
  } = options;

  ctx.strokeStyle = strokeColor;
  ctx.fillStyle = fillColor;
  ctx.lineWidth = lineWidth;
  ctx.font = `${fontSize}px Arial`;

  boxes.forEach((box) => {
    // Draw bounding box
    ctx.strokeRect(box.x, box.y, box.width, box.height);
    ctx.fillRect(box.x, box.y, box.width, box.height);

    // Draw label background
    const labelText = `${box.label} ${(box.confidence * 100).toFixed(0)}%`;
    const textMetrics = ctx.measureText(labelText);
    const textHeight = fontSize;
    const padding = 4;

    ctx.fillStyle = strokeColor;
    ctx.fillRect(
      box.x,
      box.y - textHeight - padding * 2,
      textMetrics.width + padding * 2,
      textHeight + padding * 2
    );

    // Draw label text
    ctx.fillStyle = textColor;
    ctx.fillText(labelText, box.x + padding, box.y - padding);

    // Reset fill style
    ctx.fillStyle = fillColor;
  });
}

/**
 * Draw center grid overlay
 */
export function drawCenterGrid(
  canvas: HTMLCanvasElement,
  options: {
    color?: string;
    lineWidth?: number;
    opacity?: number;
  } = {}
) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const {
    color = '#ffffff',
    lineWidth = 1,
    opacity = 0.3,
  } = options;

  const { width, height } = canvas;
  const centerX = width / 2;
  const centerY = height / 2;

  ctx.save();
  ctx.globalAlpha = opacity;
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.setLineDash([5, 5]);

  // Vertical center line
  ctx.beginPath();
  ctx.moveTo(centerX, 0);
  ctx.lineTo(centerX, height);
  ctx.stroke();

  // Horizontal center line
  ctx.beginPath();
  ctx.moveTo(0, centerY);
  ctx.lineTo(width, centerY);
  ctx.stroke();

  // Quadrant lines
  const quarterX = width / 4;
  const quarterY = height / 4;

  // Vertical quarters
  ctx.beginPath();
  ctx.moveTo(quarterX, 0);
  ctx.lineTo(quarterX, height);
  ctx.moveTo(width - quarterX, 0);
  ctx.lineTo(width - quarterX, height);
  ctx.stroke();

  // Horizontal quarters
  ctx.beginPath();
  ctx.moveTo(0, quarterY);
  ctx.lineTo(width, quarterY);
  ctx.moveTo(0, height - quarterY);
  ctx.lineTo(width, height - quarterY);
  ctx.stroke();

  ctx.restore();
}

/**
 * Clear canvas
 */
export function clearCanvas(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

/**
 * Resize canvas to match video dimensions
 */
export function resizeCanvas(canvas: HTMLCanvasElement, video: HTMLVideoElement) {
  canvas.width = video.videoWidth || video.clientWidth;
  canvas.height = video.videoHeight || video.clientHeight;
}

/**
 * Draw status text overlay
 */
export function drawStatusText(
  canvas: HTMLCanvasElement,
  text: string,
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' = 'top-left',
  options: {
    color?: string;
    backgroundColor?: string;
    fontSize?: number;
    padding?: number;
  } = {}
) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const {
    color = '#ffffff',
    backgroundColor = 'rgba(0, 0, 0, 0.7)',
    fontSize = 14,
    padding = 8,
  } = options;

  ctx.font = `${fontSize}px Arial`;
  const textMetrics = ctx.measureText(text);
  const textWidth = textMetrics.width;
  const textHeight = fontSize;

  let x, y;
  
  switch (position) {
    case 'top-left':
      x = padding;
      y = padding + textHeight;
      break;
    case 'top-right':
      x = canvas.width - textWidth - padding;
      y = padding + textHeight;
      break;
    case 'bottom-left':
      x = padding;
      y = canvas.height - padding;
      break;
    case 'bottom-right':
      x = canvas.width - textWidth - padding;
      y = canvas.height - padding;
      break;
  }

  // Draw background
  ctx.fillStyle = backgroundColor;
  ctx.fillRect(x - padding/2, y - textHeight - padding/2, textWidth + padding, textHeight + padding);

  // Draw text
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}