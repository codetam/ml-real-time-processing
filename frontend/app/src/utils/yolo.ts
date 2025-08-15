interface Bbox {
  x_min: number,
  y_min: number,
  x_max: number,
  y_max: number
}
interface Detection {
  label: string,
  confidence: number,
  bbox: Bbox
}

export async function generateImageWithBBoxes(file: File, detections: Detection[]) {
  return new Promise<string>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return reject('No canvas context');

      // Draw original image
      ctx.drawImage(img, 0, 0);

      detections.forEach((detection) => {
        // Draw bounding box
        ctx.strokeStyle = 'limegreen';
        ctx.lineWidth = 4;
        ctx.strokeRect(detection.bbox.x_min,
          detection.bbox.y_min,
          detection.bbox.x_max - detection.bbox.x_min,
          detection.bbox.y_max - detection.bbox.y_min);

        // Draw label
        ctx.fillStyle = 'limegreen';
        ctx.font = '32px sans-serif';
        const label = `${detection.label}: ${detection.confidence}`;
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(detection.bbox.x_min, detection.bbox.y_min - 36, textWidth + 10, 36);

        ctx.fillStyle = 'white';
        ctx.fillText(label, detection.bbox.x_min + 5, detection.bbox.y_min - 8);
      });
      // Export new image as Data URL
      resolve(canvas.toDataURL('image/png'));
    }

    img.onerror = (err) => reject(err);
    img.src = URL.createObjectURL(file);
  });
}