
// Cache buster for enhanced pathologies
window.ENHANCED_PATHOLOGY_VERSION = '20250830_193203';

// Add cache buster to all API requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
    if (args[0] && args[0].includes('/api/')) {
        const url = new URL(args[0], window.location.origin);
        url.searchParams.set('v', window.ENHANCED_PATHOLOGY_VERSION);
        args[0] = url.toString();
    }
    return originalFetch.apply(this, args);
};

console.log('🚀 Enhanced pathology cache buster active:', window.ENHANCED_PATHOLOGY_VERSION);
