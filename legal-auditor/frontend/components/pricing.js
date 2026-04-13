/**
 * Pricing Component — Handles Credit purchases
 */
async function renderPricing(container) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1>Buy Audit Credits</h1>
                <p>Choose a pack to replenish your auditing power</p>
            </div>
        </div>

        <div class="pricing-grid">
            <div class="pricing-card glass-panel" style="animation-delay: 0.1s">
                <div class="plan-badge">Most Flexible</div>
                <h3>Starter Pack</h3>
                <div class="plan-price">$5</div>
                <div class="plan-credits">5 Credits</div>
                <ul class="plan-features">
                    <li>5 Full Document Audits</li>
                    <li>24/7 AI Chat Access</li>
                    <li>PDF Report Export</li>
                    <li>Basic Support</li>
                </ul>
                <button class="btn btn-secondary" onclick="handleBuyCredits('starter')">Get Started</button>
            </div>

            <div class="pricing-card glass-panel featured" style="animation-delay: 0.2s">
                <div class="plan-badge primary">Best Value</div>
                <h3>Professional Pack</h3>
                <div class="plan-price">$15</div>
                <div class="plan-credits">20 Credits</div>
                <ul class="plan-features">
                    <li>20 Full Document Audits</li>
                    <li>Priority AI Queue</li>
                    <li>PDF Report Export</li>
                    <li>Custom Audit Types</li>
                    <li>Priority Support</li>
                </ul>
                <button class="btn btn-primary" onclick="handleBuyCredits('pro')">Upgrade Now</button>
            </div>

            <div class="pricing-card glass-panel" style="animation-delay: 0.3s">
                <div class="plan-badge">Scale</div>
                <h3>Enterprise Pack</h3>
                <div class="plan-price">$50</div>
                <div class="plan-credits">100 Credits</div>
                <ul class="plan-features">
                    <li>100 Full Document Audits</li>
                    <li>Highest Priority Queue</li>
                    <li>Unlimited Chat History</li>
                    <li>Advanced Risk Analytics</li>
                    <li>Dedicated Support</li>
                </ul>
                <button class="btn btn-secondary" onclick="handleBuyCredits('enterprise')">Buy Pack</button>
            </div>
        </div>

        <div class="pricing-footer glass-panel">
            <div class="footer-info">
                <h4>Secure Payments via Stripe</h4>
                <p>All transactions are securely processed. We do not store your card details.</p>
            </div>
            <div class="stripe-badges">
                <svg viewBox="0 0 40 16" width="40" height="16" fill="currentColor"><path d="M36.19 8.24c0-2.31-1.12-3.81-3.23-3.81-2.07 0-3.35 1.76-3.35 4s1.39 4.09 3.51 4.09a3.54 3.54 0 0 0 3-.62l.06-.06-.5-.38.06-.06a2.69 2.69 0 0 1-2.58.58c-1.34 0-2-1.07-2-2.34h5.08c0-.12.06-1.19.06-1.4zM32.19 7.5c0-.84.44-1.63 1.25-1.63s1.25.79 1.25 1.63h-2.5zm-5.75-2.94a2.76 2.76 0 0 0-1.84-.75c-1.25 0-2.06.69-2.06 1.78 0 2.5 3.31 1.63 3.31 3.5 0 .69-.69.88-1.25.88a2.59 2.59 0 0 1-1.62-.63l-.06-.06-.44.37-.06.06a3.47 3.47 0 0 0 2.13.81c1.31 0 2.19-.62 2.19-1.81 0-2.56-3.31-1.62-3.31-3.5 0-.5.5-.81 1.25-.81a2.12 2.12 0 0 1 1.5.56l.06.06.38-.38.07-.07zm-7.69.5h-2.12v1.5h2.12a.66.66 0 0 1 .69.69.67.67 0 0 1-.69.69h-2.12v2.75l-1-.44v-5.25h-1v-1l1-.44v-1.19a2.07 2.07 0 0 1 2.25-2.25 2.16 2.16 0 0 1 1.5.62l.06.06-.5.75-.06-.06a1.18 1.18 0 0 0-.94-.38c-.69 0-1 .44-1 1.25v.75h2.12v.44l-1 .44zm-5.44.81l.06.06.56-.37-.06-.06a4.13 4.13 0 0 0-2.25-.63c-2.13 0-3.38 1.63-3.38 4s1.25 4.13 3.38 4.13a4.05 4.05 0 0 0 2.31-.69l.06-.06-.12-.88-.06.06a3.14 3.14 0 0 1-2.13.75c-1.31 0-2.31-.75-2.31-3.25s1.07-3.25 2.19-3.25a2.76 2.76 0 0 1 1.81.75zm-6.06-2.25l-1 .44V10.5l-1 .44V1l-1 .44v9.06l-1 .44V4.5l-1 .44v6.5a1.11 1.11 0 0 0 1.19 1.19c.38 0 .63-.06.81-.13l.06-.06.13-.81.06.06a2.15 2.15 0 0 0 1.44.56c1.31 0 1.88-1.5 1.88-1.5a3.84 3.84 0 0 0 1.88 1.5c1.19 0 2.25-.56 2.25-1.38V4.5l-1 .44v5.38c0 .31-.19.5-.5.5s-.5-.19-.5-.5V4.63l-1 .43v5.25c0 .31-.19.5-.5.5s-.5-.19-.5-.5V4.63l-1 .43v5.25c0 .31-.19.5-.5.5s-.5-.19-.5-.5V3.81c0-.56.63-.75.63-.75l.13-.81c-.13-.19-.38-.25-.63-.25z"/></svg>
            </div>
        </div>
    `;
}

async function handleBuyCredits(planId) {
    try {
        const res = await api.post('/api/payments/create-checkout-session', { plan_id: planId });
        if (res.url) {
            window.location.href = res.url;
        } else {
            throw new Error('Could not create payment session');
        }
    } catch (err) {
        showToast(err.message || 'Payment initiation failed', 'error');
    }
}
