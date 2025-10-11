/**
 * Weather Effects for ALERTICA
 * This script adds dynamic background effects based on alert types
 */

// Map of alert types to their corresponding effects
const alertTypeEffects = {
    'rain': 'rain-effect',
    'storm': 'storm-effect',
    'flood': 'flood-effect',
    'snow': 'snow-effect',
    'fire': 'fire-effect',
    'heat': 'fire-effect',
    'earthquake': 'earthquake-effect',
    'tornado': 'storm-effect',
    'hurricane': 'storm-effect',
    'tsunami': 'flood-effect',
    'default': ''
};

// Function to apply weather effect based on alert type
function applyWeatherEffect(alertType) {
    // Remove any existing weather effects
    removeAllWeatherEffects();
    
    // Convert alert type to lowercase and remove spaces
    const type = alertType.toLowerCase().replace(/\s+/g, '');
    
    // Find the matching effect or use default (no effect)
    const effectClass = alertTypeEffects[type] || '';
    
    if (effectClass) {
        // Create weather effect element
        const effectElement = document.createElement('div');
        effectElement.className = `weather-effect ${effectClass}`;
        effectElement.id = 'weather-effect-container';
        
        // Add to body
        document.body.appendChild(effectElement);
        
        console.log(`Applied ${effectClass} for alert type: ${alertType}`);
    }
}

// Function to remove all weather effects
function removeAllWeatherEffects() {
    const existingEffect = document.getElementById('weather-effect-container');
    if (existingEffect) {
        existingEffect.remove();
    }
}

// Initialize weather effects when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on an alert details page
    const alertMetaElements = document.querySelectorAll('.alert-meta strong');
    
    alertMetaElements.forEach(function(element) {
        if (element.textContent.includes('Type:')) {
            // Extract alert type from the page
            const alertTypeText = element.parentNode.textContent;
            const alertType = alertTypeText.replace('Type:', '').trim();
            
            // Apply the appropriate weather effect
            applyWeatherEffect(alertType);
        }
    });
    
    // For dashboard page, apply effect when alert type is selected
    const alertTypeSelect = document.getElementById('alert_type');
    if (alertTypeSelect) {
        alertTypeSelect.addEventListener('change', function() {
            applyWeatherEffect(this.value);
        });
    }
});