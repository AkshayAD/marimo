// Check if URL ends with .html and redirect
if (window.location.pathname.endsWith('.html')) {
  const redirectUrl = window.location.pathname.slice(0, -5) + window.location.search + window.location.hash;
  console.log('Redirecting to', redirectUrl);
  window.location.href = redirectUrl;
}

// Analytics removed - No tracking
