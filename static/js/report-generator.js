class ReportGenerator {
  constructor() {
    this.targetRowIds = ["1757322288349", "1757322711026"];
  }

  async fetchApiData(companyId, fromDate, toDate) {
    const response = await fetch(`http://localhost:5000/api/data`);
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    return data;
  }

  generateAnalytics(reportData) {
    // Add safety checks for data structure
    const safeGet = (obj, path, defaultValue = []) => {
      try {
        return path.split(".").reduce((o, p) => o && o[p], obj) || defaultValue;
      } catch  {
        return defaultValue;
      }
    };

    return {
      totalRecords: safeGet(reportData, "overall_stats.total_feedback", 0),
      sentimentBreakdown: safeGet(reportData, "audio_metrics.sentiment_distribution", {}),
      averageRatings: safeGet(reportData, "survey_metrics.question_averages", {}),
      recommendations: safeGet(reportData, "audio_metrics.recommendations", []),
      positiveThemes: safeGet(reportData, "audio_metrics.positive_themes", []),
      negativeThemes: safeGet(reportData, "audio_metrics.negative_themes", [])
    };
  }

  generateStarRating(rating) {
    const full = Math.floor(rating);
    const half = rating - full >= 0.5
      ? 1
      : 0;
    const empty = 5 - full - half;
    return `<span class="rating-stars">${ "★".repeat(full)}${ "½".repeat(half)}${ "☆".repeat(empty)}</span> ${rating}`;
  }

  generateChartHtml(analytics) {
    const total = analytics.totalRecords;
    const positive = analytics.sentimentBreakdown.Positive || 0;
    const neutral = analytics.sentimentBreakdown.Neutral || 0;
    const negative = analytics.sentimentBreakdown.Negative || 0;

    const sentimentChart = this.generateSentimentChart(positive, neutral, negative);

    return {sentimentChart};
  }

  generateSentimentChart(positive, neutral, negative) {
    const total = positive + neutral + negative;
    if (total === 0) 
      return '<div class="text-muted">No data available</div>';
    
    const posPercent = Math.round((positive / total) * 100);
    const neuPercent = Math.round((neutral / total) * 100);
    const negPercent = Math.round((negative / total) * 100);

    return `
            <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
                <svg width="200" height="200" viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" stroke-width="20"/>
                    <circle cx="100" cy="100" r="80" fill="none" stroke="#10b981" stroke-width="20" 
                            stroke-dasharray="${posPercent * 5.03} 502" stroke-dashoffset="0" transform="rotate(-90 100 100)"/>
                    <circle cx="100" cy="100" r="80" fill="none" stroke="#f59e0b" stroke-width="20" 
                            stroke-dasharray="${neuPercent * 5.03} 502" stroke-dashoffset="-${posPercent * 5.03}" transform="rotate(-90 100 100)"/>
                    <circle cx="100" cy="100" r="80" fill="none" stroke="#ef4444" stroke-width="20" 
                            stroke-dasharray="${negPercent * 5.03} 502" stroke-dashoffset="-${ (posPercent + neuPercent) * 5.03}" transform="rotate(-90 100 100)"/>
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                    <div style="font-size: 24px; font-weight: bold;">${total}</div>
                    <div style="font-size: 12px; color: #666;">Reviews</div>
                </div>
            </div>
            <div style="display: flex; justify-content: center; gap: 16px; margin-top: 16px; font-size: 12px;">
                <div><span style="color: #10b981;">●</span> Positive ${posPercent}%</div>
                <div><span style="color: #f59e0b;">●</span> Neutral ${neuPercent}%</div>
                <div><span style="color: #ef4444;">●</span> Negative ${negPercent}%</div>
            </div>
        `;
  }

  generateHtmlReport(analytics, companyName, reportData) {
    const currentTime = new Date();
    const weekStart = new Date(currentTime.getTime() - 7 * 24 * 60 * 60 * 1000);
    const weekEnd = currentTime;

    const clientData = {
      company_name: companyName,
      company_city: "Singapore",
      company_industry: "FNB",
      total_reviews: analytics.totalRecords,
      positive_reviews: analytics.sentimentBreakdown.Positive || 0,
      neutral_reviews: analytics.sentimentBreakdown.Neutral || 0,
      negative_reviews: analytics.sentimentBreakdown.Negative || 0,
      positive_themes: analytics.positiveThemes.slice(0, 5),
      negative_themes: analytics.negativeThemes.slice(0, 5),
      notable_quotes: analytics.recommendations.slice(0, 3),
      top_questions: Object.entries(analytics.averageRatings),
      recommendation: analytics.recommendations.join(". "),
      nps_score: 65
    };

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${
    clientData.company_name} Weekly Analytics Report - InstaReview.ai</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: white; color: #1e293b; }
        .page { width: 100%; min-height: 100vh; padding: 30px 15px; background: white; }
        .kpi-value { font-size: 24px; font-weight: 800; }
        .kpi-label { font-size: 10px; color: #64748b; font-weight: 500; }
        .comparison { font-size: 10px; margin-top: 4px; }
        .trend-up { color: #10b981; } .trend-down { color: #ef4444; }
        .chart-title { font-size: 12px; font-weight: 700; margin-bottom: 8px; text-align: center; }
        .insight-card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; height: 100%; }
        .insight-title { font-size: 12px; font-weight: 700; margin-bottom: 8px; }
        .questions-table { width: 100%; border-collapse: collapse; font-size: 10px; }
        .questions-table th, .questions-table td { padding: 4px; text-align: left; border-bottom: 1px solid #e2e8f0; }
        .questions-table th { background: #f8fafc; font-weight: 600; color: #64748b; }
        .rating-stars { color: #fbbf24; }
        .theme-list { list-style: none; display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
        .theme-tag { background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 12px; font-size: 10px; }
        .theme-tag.negative { background: #fef2f2; color: #dc2626; }
        .quotes { font-size: 10px; }
        .quote { font-style: italic; color: #64748b; margin-bottom: 4px; padding: 6px; background: #f8fafc; border-radius: 4px; border-left: 2px solid #3b82f6; }
    </style>
</head>
<body>
    <div class="page container-fluid">
        <div class="row g-3 mb-3">
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-star text-warning"></i> ${
    clientData.total_reviews}</div><div class="kpi-label">Total Reviews</div><div class="comparison trend-up"><i class="fas fa-arrow-up"></i> 15%</div></div></div>
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-smile text-success"></i> ${Math.round((clientData.positive_reviews / clientData.total_reviews) * 100)}%</div><div class="kpi-label">Positive</div><div class="comparison trend-up"><i class="fas fa-arrow-up"></i> 3%</div></div></div>
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-meh text-secondary"></i> ${Math.round((clientData.neutral_reviews / clientData.total_reviews) * 100)}%</div><div class="kpi-label">Neutral</div><div class="comparison"><i class="fas fa-minus"></i> 0%</div></div></div>
            <div class="col-3"><div class="border rounded p-3 text-center h-100 d-flex flex-column justify-content-between"><div class="kpi-value"><i class="fas fa-frown text-danger"></i> ${Math.round((clientData.negative_reviews / clientData.total_reviews) * 100)}%</div><div class="kpi-label">Negative</div><div class="comparison trend-down"><i class="fas fa-arrow-down"></i> 2%</div></div></div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-chart-pie text-primary"></i> Sentiment Distribution</div>
                    ${this.generateChartHtml(analytics).sentimentChart}
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card quotes">
                    <div class="insight-title"><i class="fas fa-quote-left text-info"></i> Notable Customer Quotes</div>
                    ${clientData.notable_quotes.map(
      (quote, i) => `<div class="quote" style="border-left: 2px solid ${i === 0
      ? "#10b981"
      : i === 1
        ? "#64748b"
        : "#ef4444"}; background: ${i === 0
          ? "#f0fdf4"
          : i === 1
            ? "#f8fafc"
            : "#fef2f2"};">"${quote}"</div>`).join("")}
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-chart-bar text-primary"></i> Survey Questions Performance</div>
                    <table class="questions-table">
                        <tbody>${clientData.top_questions.map(([q, rating]) => `<tr><td>${q}</td><td>${this.generateStarRating(rating)}</td></tr>`).join("")}</tbody>
                    </table>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-lightbulb text-warning"></i> Key Recommendations</div>
                    <div style="font-size: 11px;">${
    clientData.recommendation}</div>
                </div>
            </div>
        </div>
    
    <!-- PAGE 2 -->
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-check-circle text-success"></i> Top Positive Themes</div>
                    <div class="theme-list">${clientData.positive_themes.map(theme => `<span class="theme-tag">${theme}</span>`).join("")}</div>
                    <div class="insight-title"><i class="fas fa-exclamation-triangle text-warning"></i> Areas for Improvement</div>
                    <div class="theme-list">${clientData.negative_themes.map(theme => `<span class="theme-tag negative">${theme}</span>`).join("")}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                   <div class="border rounded p-3" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);">
                    <div class="row">
                        <div class="col-8">
                            <div class="mb-2"><i class="fas fa-lightbulb text-warning"></i> <strong>Next Steps</strong></div>
                            <div style="font-size: 11px; color: #64748b;">Focus on product quality improvements based on feedback</div>
                        </div>
                        <div class="col-4 text-end">
                            <div class="mb-1"><span class="badge bg-primary">NPS Score: ${
    clientData.nps_score}</span></div>
                            <div style="font-size: 9px; color: #64748b;">Powered by InstaReview.ai</div>
                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-chart-pie text-primary"></i> Sentiment Breakdown</div>
                    <div style="font-size: 11px;">
                        <div class="mb-2 d-flex justify-content-between"><span><i class="fas fa-smile text-success"></i> Positive/span> <strong>${Math.round((clientData.positive_reviews / clientData.total_reviews) * 100)}% (${
    clientData.positive_reviews} reviews)</strong></div>
                        <div class="mb-2 d-flex justify-content-between"><span><i class="fas fa-meh text-secondary"></i> Neutral</span> <strong>${Math.round((clientData.neutral_reviews / clientData.total_reviews) * 100)}% (${
    clientData.neutral_reviews} reviews)</strong></div>
                        <div class="mb-2 d-flex justify-content-between"><span><i class="fas fa-frown text-danger"></i> Negative</span> <strong>${Math.round((clientData.negative_reviews / clientData.total_reviews) * 100)}% (${
    clientData.negative_reviews} reviews)</strong></div>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-balance-scale text-info"></i> Feedback Distribution</div>
                    <div style="font-size: 11px;">
                        <div class="mb-1">Survey Responses: ${
    Object.keys(analytics.averageRatings).length}</div>
                        <div class="mb-1">Audio Feedback: ${
    analytics.totalRecords}</div>
                        <div class="mb-1">Total Feedback: ${
    analytics.totalRecords}</div>
                        <div class="mb-1">Complaints Detected: ${
    analytics.negativeThemes.length}/${analytics.totalRecords}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-trending-up text-success"></i> Improvement Areas</div>
                    <ul style="font-size: 10px; margin: 0; padding-left: 15px;">
                        ${analytics.negativeThemes.slice(0, 4).map(theme => `<li>Address ${theme}</li>`).join("")}
                    </ul>
                </div>
            </div>
            <div class="col-6">
                <div class="insight-card">
                    <div class="insight-title"><i class="fas fa-target text-primary"></i> Success Metrics</div>
                    <div style="font-size: 11px;">
                        <div class="mb-1">Customer Satisfaction: ${
    Object.values(analytics.averageRatings).length > 0
      ? (Object.values(analytics.averageRatings).reduce((a, b) => parseFloat(a) + parseFloat(b), 0) / Object.values(analytics.averageRatings).length).toFixed(1)
      : "0"}/5</div>
                        <div class="mb-1">Response Rate: 100%</div>
                        <div class="mb-1">Feedback Quality: High</div>
                        <div class="mb-1">Action Items: ${
    analytics.recommendations.length} identified</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-12">
                
        </div>
        
        <div class="row g-3 mb-3">
            <div class="col-12">
                <div class="border rounded p-2" style="background: #fef3c7; border-color: #f59e0b;">
                    <div style="font-size: 9px; color: #92400e; text-align: left;">
                        <i class="fas fa-info-circle"></i> <strong>Disclaimer:</strong> This analysis is generated by AI based on transcript metadata and automated sentiment analysis. Results should be verified by human review for business-critical decisions.
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>`;
  }

  async generateReport(companyId, fromDate, toDate) {
    try {
      const reportData = await this.fetchApiData(companyId, fromDate, toDate);

      if (!reportData || reportData.error) {
        throw new Error(
          reportData
          ?.error || "No data available");
      }

      const analytics = this.generateAnalytics(reportData);
      const htmlReport = this.generateHtmlReport(analytics, companyId, reportData);

      window.currentAnalytics = analytics;

      return {success: true, analytics, htmlReport, recordCount: analytics.totalRecords};
    } catch (error) {
      return {success: false, error: error.message};
    }
  }
}

// Auto-initialize dashboard from script tag data attributes
document.addEventListener("DOMContentLoaded", () => {
  const scripts = document.querySelectorAll('script[src*="report-generator.js"]');
  scripts.forEach(script => {
    const containerId = script.dataset.containerId;
    const companyId = script.dataset.companyId;
    const autoRefresh = script.dataset.autoRefresh !== "false";
    const refreshInterval = parseInt(script.dataset.refreshInterval) || 60;

    if (containerId && document.getElementById(containerId)) {
      new EmbeddableDashboard({
        containerId,
        companyId: companyId || "123456789A_123456_01-01_FNB",
        autoRefresh,
        refreshInterval: refreshInterval * 1000
      });
    }
  });
});

class EmbeddableDashboard {
  constructor(options) {
    this.options = {
      apiUrl: "http://localhost:5000",
      ...options
    };
    this.reportGenerator = new ReportGenerator();
    this.charts = {};
    this.refreshTimer = null;
    this.init();
  }

  init() {
    this.render();
    this.initCharts();
    this.loadData();
    if (this.options.autoRefresh) 
      this.startAutoRefresh();
    }
  
  render() {
    const container = document.getElementById(this.options.containerId);
    container.innerHTML = `
      <div class="instareview-embed" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden;">
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 16px; display: flex; justify-content: space-between; align-items: center;">
          <h3 style="margin: 0; font-size: 18px; font-weight: 600;">📊 Live Analytics</h3>
          <div style="display: flex; align-items: center; gap: 8px; font-size: 12px;">
            <span id="embed-status" style="width: 8px; height: 8px; border-radius: 50%; background: #10b981;"></span>
            <span id="embed-status-text">Live</span>
          </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 16px;">
          <div style="text-align: center; padding: 16px; background: #f8f9fa; border-radius: 8px;">
            <div id="embed-total" style="font-size: 24px; font-weight: 700; color: #3b82f6; margin-bottom: 4px;">0</div>
            <div style="font-size: 12px; color: #666;">Total Reviews</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #f0fdf4; border-radius: 8px;">
            <div id="embed-positive" style="font-size: 24px; font-weight: 700; color: #10b981; margin-bottom: 4px;">0%</div>
            <div style="font-size: 12px; color: #666;">Positive</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #fffbeb; border-radius: 8px;">
            <div id="embed-neutral" style="font-size: 24px; font-weight: 700; color: #f59e0b; margin-bottom: 4px;">0%</div>
            <div style="font-size: 12px; color: #666;">Neutral</div>
          </div>
          <div style="text-align: center; padding: 16px; background: #fef2f2; border-radius: 8px;">
            <div id="embed-negative" style="font-size: 24px; font-weight: 700; color: #ef4444; margin-bottom: 4px;">0%</div>
            <div style="font-size: 12px; color: #666;">Negative</div>
          </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 0 16px 16px;">
          <div style="height: 200px;">
            <canvas id="embed-sentiment-chart"></canvas>
          </div>
          <div style="height: 200px;">
            <canvas id="embed-ratings-chart"></canvas>
          </div>
        </div>
        
        <div style="padding: 16px; border-top: 1px solid #e5e5e5; background: #f8f9fa;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div>
              <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #10b981;">✓ Positive Themes</div>
              <div id="embed-positive-themes"></div>
            </div>
            <div>
              <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #ef4444;">⚠ Areas for Improvement</div>
              <div id="embed-negative-themes"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  initCharts() {
    this.charts.sentiment = new Chart(document.getElementById("embed-sentiment-chart"), {
      type: "doughnut",
      data: {
        labels: [
          "Positive", "Neutral", "Negative"
        ],
        datasets: [
          {
            data: [
              0, 0, 0
            ],
            backgroundColor: [
              "#10b981", "#f59e0b", "#ef4444"
            ],
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              fontSize: 10
            }
          }
        }
      }
    });

    this.charts.ratings = new Chart(document.getElementById("embed-ratings-chart"), {
      type: "bar",
      data: {
        labels: [],
        datasets: [
          {
            data: [],
            backgroundColor: "#3b82f6",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 5
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  async loadData() {
    try {
      document.getElementById("embed-status-text").textContent = "Loading...";
      const now = new Date();
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

      const result = await this.reportGenerator.generateReport(this.options.companyId, weekAgo.toISOString(), now.toISOString());

      if (result.success) {
        this.updateDisplay(result.analytics);
        document.getElementById("embed-status-text").textContent = "Live";
        document.getElementById("embed-status").style.background = "#10b981";
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      document.getElementById("embed-status-text").textContent = "Error";
      document.getElementById("embed-status").style.background = "#ef4444";
    }
  }

  updateDisplay(analytics) {
    const total = analytics.totalRecords;
    const positive = analytics.sentimentBreakdown.Positive || 0;
    const neutral = analytics.sentimentBreakdown.Neutral || 0;
    const negative = analytics.sentimentBreakdown.Negative || 0;

    document.getElementById("embed-total").textContent = total;
    document.getElementById("embed-positive").textContent = total > 0
      ? Math.round((positive / total) * 100) + "%"
      : "0%";
    document.getElementById("embed-neutral").textContent = total > 0
      ? Math.round((neutral / total) * 100) + "%"
      : "0%";
    document.getElementById("embed-negative").textContent = total > 0
      ? Math.round((negative / total) * 100) + "%"
      : "0%";

    // Update charts
    this.charts.sentiment.data.datasets[0].data = [positive, neutral, negative];
    this.charts.sentiment.update();

    const ratings = Object.entries(analytics.averageRatings);
    this.charts.ratings.data.labels = ratings.map(([q]) => q.substring(0, 10));
    this.charts.ratings.data.datasets[0].data = ratings.map(([, r]) => parseFloat(r));
    this.charts.ratings.update();

    // Update themes
    document.getElementById("embed-positive-themes").innerHTML = analytics.positiveThemes.slice(0, 3).map(theme => `<span style="display: inline-block; padding: 2px 6px; margin: 1px; border-radius: 8px; font-size: 10px; background: #dcfce7; color: #166534;">${theme}</span>`).join("");

    document.getElementById("embed-negative-themes").innerHTML = analytics.negativeThemes.slice(0, 3).map(theme => `<span style="display: inline-block; padding: 2px 6px; margin: 1px; border-radius: 8px; font-size: 10px; background: #fee2e2; color: #991b1b;">${theme}</span>`).join("");
  }

  startAutoRefresh() {
    this.refreshTimer = setInterval(() => this.loadData(), this.options.refreshInterval);
  }

  destroy() {
    if (this.refreshTimer) 
      clearInterval(this.refreshTimer);
    Object.values(this.charts).forEach(chart => chart.destroy());
  }
}

window.ReportGenerator = ReportGenerator;
window.EmbeddableDashboard = EmbeddableDashboard;