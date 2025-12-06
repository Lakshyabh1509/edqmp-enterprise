/**
 * EDQMP API Client
 * Handles authenticated communication with the FastAPI backend
 */

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    /**
     * Helper to perform authenticated requests
     */
    async fetch(endpoint, options = {}) {
        if (!supabaseClient) {
            throw new Error("Authentication client not initialized");
        }

        const { data: { session } } = await supabaseClient.auth.getSession();

        if (!session) {
            throw new Error("No active session");
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
            ...options.headers
        };

        const config = {
            ...options,
            headers
        };

        const response = await fetch(`${this.baseUrl}${endpoint}`, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `Request failed: ${response.statusText}`);
        }

        if (response.status === 204) return null;

        try {
            return await response.json();
        } catch {
            return null;
        }
    }

    // =========================================================================
    // Data Quality
    // =========================================================================

    async getQualityRules() {
        return this.fetch('/quality/rules');
    }

    async createQualityRule(data) {
        return this.fetch('/quality/rules', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getDataSources() {
        return this.fetch('/quality/sources');
    }

    async runValidation(data, ruleIds = null) {
        // Only supports JSON data for now in this MVP
        return this.fetch('/quality/validate', {
            method: 'POST',
            body: JSON.stringify({
                source_id: '00000000-0000-0000-0000-000000000000', // Placeholder for now
                data: data,
                rule_ids: ruleIds
            })
        });
    }

    // =========================================================================
    // Pipelines
    // =========================================================================

    async getPipelineHealth() {
        return this.fetch('/pipelines/health');
    }

    async getPipelineRuns(sourceId = null) {
        const query = sourceId ? `?source_id=${sourceId}` : '';
        return this.fetch(`/pipelines/runs${query}`);
    }

    // =========================================================================
    // Alerts
    // =========================================================================

    async getAlerts() {
        return this.fetch('/alerts/history');
    }

    async getAlertStats() {
        return this.fetch('/alerts/stats');
    }

    async acknowledgeAlert(alertId) {
        return this.fetch('/alerts/acknowledge', {
            method: 'POST',
            body: JSON.stringify({ alert_id: alertId })
        });
    }
}

// Export a global instance
window.ApiClient = ApiClient;
