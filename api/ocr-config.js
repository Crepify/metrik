/**
 * Vercel serverless configuration endpoint.
 * Set OCR_API_URL in Vercel Project → Settings → Environment Variables, then redeploy.
 * This exposes only the public backend base URL to the browser; never place secrets here.
 */
module.exports = function handler(req, res) {
  const base = (process.env.OCR_API_URL || process.env.NEXT_PUBLIC_API_URL || '').replace(/\/+$/, '');
  res.setHeader('Cache-Control', 'no-store, max-age=0');
  res.status(200).json({ api_url: base });
};
