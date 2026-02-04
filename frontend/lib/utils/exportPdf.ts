"use client";

import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

interface ExportPdfOptions {
  filename: string;
  title?: string;
  subtitle?: string;
}

/**
 * Export a DOM element to PDF
 * @param elementId The ID of the element to capture
 * @param options PDF export options
 */
export async function exportToPdf(
  elementId: string,
  options: ExportPdfOptions
): Promise<void> {
  const element = document.getElementById(elementId);
  if (!element) {
    throw new Error(`Element with ID "${elementId}" not found`);
  }

  // Create canvas from the element
  const canvas = await html2canvas(element, {
    scale: 2, // Higher resolution
    useCORS: true,
    logging: false,
    backgroundColor: "#ffffff",
  });

  const imgData = canvas.toDataURL("image/png");
  const imgWidth = canvas.width;
  const imgHeight = canvas.height;

  // Calculate PDF dimensions (A4 size in mm)
  const pdfWidth = 210;
  const pdfHeight = 297;
  const margin = 15;
  const contentWidth = pdfWidth - margin * 2;
  const headerHeight = options.title ? 25 : 10;

  // Calculate scale to fit content width
  const scale = contentWidth / (imgWidth / 2); // Divide by 2 because of scale: 2 in html2canvas
  const scaledHeight = (imgHeight / 2) * scale;

  // Create PDF
  const pdf = new jsPDF({
    orientation: scaledHeight > pdfHeight - headerHeight - margin ? "portrait" : "portrait",
    unit: "mm",
    format: "a4",
  });

  // Add title if provided
  let yPosition = margin;
  if (options.title) {
    pdf.setFontSize(18);
    pdf.setFont("helvetica", "bold");
    pdf.text(options.title, margin, yPosition + 5);
    yPosition += 10;

    if (options.subtitle) {
      pdf.setFontSize(10);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(100, 100, 100);
      pdf.text(options.subtitle, margin, yPosition + 5);
      yPosition += 10;
    }
    yPosition += 5;
  }

  // Calculate available height for content
  const availableHeight = pdfHeight - yPosition - margin;

  // If content fits on one page
  if (scaledHeight <= availableHeight) {
    pdf.addImage(imgData, "PNG", margin, yPosition, contentWidth, scaledHeight);
  } else {
    // Multi-page PDF
    const pageContentHeight = availableHeight;
    const totalPages = Math.ceil(scaledHeight / pageContentHeight);

    for (let page = 0; page < totalPages; page++) {
      if (page > 0) {
        pdf.addPage();
        yPosition = margin;
      }

      // Calculate source coordinates for this page slice
      const sourceY = (page * pageContentHeight) / scale * 2; // Convert back to canvas coordinates
      const sourceHeight = Math.min(
        (pageContentHeight / scale) * 2,
        imgHeight - sourceY
      );
      const destHeight = sourceHeight * scale / 2;

      // Create a temporary canvas for this page slice
      const pageCanvas = document.createElement("canvas");
      pageCanvas.width = imgWidth;
      pageCanvas.height = sourceHeight;
      const ctx = pageCanvas.getContext("2d");

      if (ctx) {
        // Draw the slice from the original canvas
        ctx.drawImage(
          canvas,
          0, sourceY, imgWidth, sourceHeight,
          0, 0, imgWidth, sourceHeight
        );

        const pageImgData = pageCanvas.toDataURL("image/png");
        pdf.addImage(pageImgData, "PNG", margin, yPosition, contentWidth, destHeight);
      }
    }
  }

  // Add footer with generation date
  const totalPages = pdf.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    pdf.setPage(i);
    pdf.setFontSize(8);
    pdf.setFont("helvetica", "normal");
    pdf.setTextColor(150, 150, 150);
    const footerText = `Generated on ${new Date().toLocaleDateString()} | Page ${i} of ${totalPages}`;
    pdf.text(footerText, margin, pdfHeight - 10);
  }

  // Save the PDF
  pdf.save(options.filename);
}
