const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export interface BusinessProfileData {
    name: string;
    industry: string;
    location: string;
    website?: string;
}

export interface BusinessProfileResponse extends BusinessProfileData {
    id: number;
}

export interface BusinessProfileWithHistory extends BusinessProfileData {
    id: number;
    latest_audit_score?: number;
    latest_audit_date?: string;
}

export interface AuditReportResponse {
    id: number;
    business_id: number;
    created_at: string;
    overall_score: number;
    google_presence_score: number;
    content_score: number;
    social_score: number;
    competitor_analysis: string;
    social_analysis: string;
    actionable_steps: string;
    raw_data: string;
}

export const api = {
    async createProfile(data: BusinessProfileData): Promise<BusinessProfileResponse> {
        const response = await fetch(`${API_BASE_URL}/profiles/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error("Failed to create profile");
        }

        return response.json();
    },

    async triggerAudit(businessId: number): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/audits/run/${businessId}`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to trigger audit");
        }

        return response.json();
    },

    async getAudits(businessId: number): Promise<AuditReportResponse[]> {
        const response = await fetch(`${API_BASE_URL}/audits/${businessId}`);

        if (!response.ok) {
            throw new Error("Failed to fetch audits");
        }

        return response.json();
    },

    async getHistory(): Promise<BusinessProfileWithHistory[]> {
        const response = await fetch(`${API_BASE_URL}/profiles/history`);
        if (!response.ok) {
            throw new Error("Failed to fetch history");
        }
        return response.json();
    },

    async downloadReport(auditId: number, businessName: string): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/reports/${auditId}/pdf`);
        if (!response.ok) {
            throw new Error("Failed to download PDF");
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${businessName.replace(/\s+/g, '_')}_SEO_Audit.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    }
};
