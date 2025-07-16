/**
 * Dynamic Payment Link Generator for Landing Page
 * This creates fresh Stripe checkout sessions when needed
 */

// Payment configuration
const PAYMENT_CONFIG = {
    starter: {
        name: 'RedForge Starter Plan',
        price: 2900, // $29.00 in cents
        interval: 'month',
        description: 'Monthly subscription - Unlimited scans, watermark-free reports'
    },
    pro: {
        name: 'RedForge Pro Plan', 
        price: 9900, // $99.00 in cents
        interval: 'month',
        description: 'Professional subscription with priority support'
    }
};

// Static payment links (refresh daily)
const STATIC_PAYMENT_LINKS = {
    starter: 'https://checkout.stripe.com/c/pay/cs_live_b1TnUcNAlE848XM2OwrWZK4NG6eYsJvgKR9MUAlqizQw7lJJcYOBC8jWBQ#fidkdWxOYHwnPyd1blppbHNgWjA0V0lTZFJES1xkbHQ2R1VAUExucnFqNjxATGcxNU1xaHVGalFWfzBBSXdvdmN1Sm5yRn1rVkFdUncyQWhQd09hZEFyYFRrdm9dZldtZlRwSzZMVHx8fXFrNTU8b1AwYVd%2FYCcpJ2N3amhWYHdzYHcnP3F3cGApJ2lkfGpwcVF8dWAnPydocGlxbFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl',
    pro: 'https://checkout.stripe.com/c/pay/cs_live_b1Xe4VSxiEXqflHBMIKgqSEp7tRtIrMNLsHQmq0Xv1OTGATAgjERx3ui5B#fidkdWxOYHwnPyd1blppbHNgWjA0V0lTZFJES1xkbHQ2R1VAUExucnFqNjxATGcxNU1xaHVGalFWfzBBSXdvdmN1Sm5yRn1rVkFdUncyQWhQd09hZEFyYFRrdm9dZldtZlRwSzZMVHx8fXFrNTU8b1AwYVd%2FYCcpJ2N3amhWYHdzYHcnP3F3cGApJ2lkfGpwcVF8dWAnPydocGlxbFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl'
};

/**
 * Handle payment button clicks
 */
function handlePaymentClick(plan) {
    // Add loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    button.disabled = true;
    
    // Track analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'payment_click', {
            'event_category': 'conversion',
            'event_label': plan,
            'value': PAYMENT_CONFIG[plan].price / 100
        });
    }
    
    // Use static payment link
    const paymentUrl = STATIC_PAYMENT_LINKS[plan];
    
    if (paymentUrl) {
        // Open payment in same tab
        window.location.href = paymentUrl;
    } else {
        // Fallback: show error
        alert('Payment link temporarily unavailable. Please try again in a moment.');
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

/**
 * Initialize payment buttons
 */
function initializePaymentButtons() {
    // Add event listeners to payment buttons
    document.addEventListener('DOMContentLoaded', function() {
        const starterButtons = document.querySelectorAll('[data-payment="starter"]');
        const proButtons = document.querySelectorAll('[data-payment="pro"]');
        
        starterButtons.forEach(button => {
            button.addEventListener('click', () => handlePaymentClick('starter'));
        });
        
        proButtons.forEach(button => {
            button.addEventListener('click', () => handlePaymentClick('pro'));
        });
    });
}

// Initialize when script loads
initializePaymentButtons();