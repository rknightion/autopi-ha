/* SEO enhancements for AutoPi Home Assistant Integration documentation */

document.addEventListener('DOMContentLoaded', function() {
  addStructuredData();
  enhanceMetaTags();
  addOpenGraphTags();
  addTwitterCardTags();
  addCanonicalURL();
});

// Add JSON-LD structured data
function addStructuredData() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "AutoPi Home Assistant Integration",
    "applicationCategory": "Vehicle Monitoring Software",
    "operatingSystem": "Home Assistant",
    "description": "A comprehensive Home Assistant custom integration for monitoring AutoPi vehicle tracking devices with real-time OBD-II diagnostics and GPS data",
    "url": "https://m7kni.io/autopi-ha/",
    "downloadUrl": "https://github.com/rknightion/autopi-ha",
    "softwareVersion": "latest",
    "programmingLanguage": "Python",
    "license": "https://github.com/rknightion/autopi-ha/blob/main/LICENSE",
    "author": {
      "@type": "Person",
      "name": "Rob Knighton",
      "url": "https://github.com/rknightion"
    },
    "maintainer": {
      "@type": "Person",
      "name": "Rob Knighton",
      "url": "https://github.com/rknightion"
    },
    "codeRepository": "https://github.com/rknightion/autopi-ha",
    "programmingLanguage": [
      "Python",
      "YAML"
    ],
    "runtimePlatform": [
      "Home Assistant",
      "Python 3.12+"
    ],
    "applicationSubCategory": [
      "Vehicle Monitoring",
      "Home Assistant Integration",
      "AutoPi",
      "OBD-II Diagnostics"
    ],
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "screenshot": "https://m7kni.io/autopi-ha/assets/social-card.png",
    "featureList": [
      "Real-time vehicle diagnostics",
      "GPS tracking and location data",
      "OBD-II data collection",
      "Home Assistant device integration",
      "Comprehensive vehicle monitoring",
      "Automatic device discovery",
      "Production-ready integration"
    ]
  };

  // Add documentation-specific structured data
  const docData = {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    "headline": document.title,
    "description": document.querySelector('meta[name="description"]')?.content || "AutoPi Home Assistant Integration documentation",
    "url": window.location.href,
    "datePublished": document.querySelector('meta[name="date"]')?.content,
    "dateModified": document.querySelector('meta[name="git-revision-date-localized"]')?.content,
    "author": {
      "@type": "Person",
      "name": "Rob Knighton"
    },
    "publisher": {
      "@type": "Organization",
      "name": "AutoPi Home Assistant Integration",
      "url": "https://m7kni.io/autopi-ha/"
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": window.location.href
    },
    "articleSection": getDocumentationSection(),
    "keywords": getPageKeywords(),
    "about": {
      "@type": "SoftwareApplication",
      "name": "AutoPi Home Assistant Integration"
    }
  };

  // Insert structured data
  const script1 = document.createElement('script');
  script1.type = 'application/ld+json';
  script1.textContent = JSON.stringify(structuredData);
  document.head.appendChild(script1);

  const script2 = document.createElement('script');
  script2.type = 'application/ld+json';
  script2.textContent = JSON.stringify(docData);
  document.head.appendChild(script2);
}

// Enhance existing meta tags
function enhanceMetaTags() {
  // Add robots meta if not present
  if (!document.querySelector('meta[name="robots"]')) {
    addMetaTag('name', 'robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1');
  }

  // Add language meta
  addMetaTag('name', 'language', 'en');

  // Add content type
  addMetaTag('http-equiv', 'Content-Type', 'text/html; charset=utf-8');

  // Add viewport if not present (should be handled by Material theme)
  if (!document.querySelector('meta[name="viewport"]')) {
    addMetaTag('name', 'viewport', 'width=device-width, initial-scale=1');
  }

  // Add keywords based on page content
  const keywords = getPageKeywords();
  if (keywords) {
    addMetaTag('name', 'keywords', keywords);
  }

  // Add article tags for documentation pages
  if (isDocumentationPage()) {
    addMetaTag('name', 'article:tag', 'home-assistant');
    addMetaTag('name', 'article:tag', 'vehicle-tracking');
    addMetaTag('name', 'article:tag', 'autopi');
    addMetaTag('name', 'article:tag', 'obd-diagnostics');
  }
}

// Add Open Graph tags
function addOpenGraphTags() {
  const title = document.title || 'AutoPi Home Assistant Integration';
  const description = document.querySelector('meta[name="description"]')?.content ||
    'Comprehensive Home Assistant integration for AutoPi vehicle tracking devices with real-time OBD-II diagnostics and GPS data';
  const url = window.location.href;
  const siteName = 'AutoPi Home Assistant Integration Documentation';

  addMetaTag('property', 'og:type', 'website');
  addMetaTag('property', 'og:site_name', siteName);
  addMetaTag('property', 'og:title', title);
  addMetaTag('property', 'og:description', description);
  addMetaTag('property', 'og:url', url);
  addMetaTag('property', 'og:locale', 'en_US');
  addMetaTag('property', 'og:image', 'https://m7kni.io/autopi-ha/assets/social-card.png');
  addMetaTag('property', 'og:image:width', '1200');
  addMetaTag('property', 'og:image:height', '630');
  addMetaTag('property', 'og:image:alt', 'AutoPi Home Assistant Integration - Vehicle monitoring for Home Assistant');
}

// Add Twitter Card tags
function addTwitterCardTags() {
  const title = document.title || 'AutoPi Home Assistant Integration';
  const description = document.querySelector('meta[name="description"]')?.content ||
    'Comprehensive Home Assistant integration for AutoPi vehicle tracking devices with real-time OBD-II diagnostics and GPS data';

  addMetaTag('name', 'twitter:card', 'summary_large_image');
  addMetaTag('name', 'twitter:title', title);
  addMetaTag('name', 'twitter:description', description);
  addMetaTag('name', 'twitter:image', 'https://m7kni.io/autopi-ha/assets/social-card.png');
  addMetaTag('name', 'twitter:creator', '@rknightion');
  addMetaTag('name', 'twitter:site', '@rknightion');
}

// Add canonical URL
function addCanonicalURL() {
  if (!document.querySelector('link[rel="canonical"]')) {
    const canonical = document.createElement('link');
    canonical.rel = 'canonical';
    canonical.href = window.location.href;
    document.head.appendChild(canonical);
  }
}

// Helper functions
function addMetaTag(attribute, name, content) {
  if (!document.querySelector(`meta[${attribute}="${name}"]`)) {
    const meta = document.createElement('meta');
    meta.setAttribute(attribute, name);
    meta.content = content;
    document.head.appendChild(meta);
  }
}

function getDocumentationSection() {
  const path = window.location.pathname;
  if (path.includes('/vehicle-data/')) return 'Vehicle Data Reference';
  if (path.includes('/api/')) return 'API Reference';
  if (path.includes('/config/')) return 'Configuration';
  if (path.includes('/installation/')) return 'Installation';
  if (path.includes('/getting-started/')) return 'Getting Started';
  if (path.includes('/development/')) return 'Development';
  return 'Documentation';
}

function getPageKeywords() {
  const path = window.location.pathname;
  const title = document.title.toLowerCase();
  const content = document.body.textContent.toLowerCase();

  let keywords = ['autopi', 'home-assistant', 'vehicle', 'obd', 'gps', 'tracking'];

  // Add path-specific keywords
  if (path.includes('/vehicle-data/')) keywords.push('diagnostics', 'telemetry', 'obd-ii');
  if (path.includes('/api/')) keywords.push('api', 'integration', 'configuration');
  if (path.includes('/config/')) keywords.push('configuration', 'setup', 'installation');
  if (path.includes('/installation/')) keywords.push('installation', 'hacs', 'custom-component');
  if (path.includes('/getting-started/')) keywords.push('tutorial', 'quick-start', 'guide');

  // Add data type keywords if mentioned
  if (content.includes('rpm') || content.includes('engine')) keywords.push('engine', 'rpm', 'diagnostics');
  if (content.includes('gps') || content.includes('location')) keywords.push('gps', 'location', 'tracking');
  if (content.includes('fuel') || content.includes('consumption')) keywords.push('fuel', 'consumption', 'efficiency');
  if (content.includes('speed') || content.includes('velocity')) keywords.push('speed', 'velocity', 'monitoring');
  if (content.includes('temperature')) keywords.push('temperature', 'coolant', 'sensors');

  return keywords.join(', ');
}

function isDocumentationPage() {
  return !window.location.pathname.endsWith('/') ||
         window.location.pathname.includes('/docs/');
}
