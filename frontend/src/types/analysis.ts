export interface AnalysisResponse {
  symbol: string
  analysis: {
    company_summary: string
    valuation?: { score: number; factors: string[] }
    trend?: { score: number; factors: string[] }
    risk?: { score: number; factors: string[] }
    strengths?: string[]
    weaknesses?: string[]
    key_metrics?: Record<string, number | null>
    key_metrics_analysis?: Record<string, string>
    overall_assessment: string
    confidence_score: number
    source?: string
  }
}
