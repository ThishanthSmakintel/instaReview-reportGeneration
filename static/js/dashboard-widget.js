class InstaReviewWidget {
  constructor(options = {}) {
    this.options = {
      containerId: options.containerId || 'instareview-widget',
      companyId: options.companyId || '123456789A_123456_01-01_FNB',
      apiUrl: options.apiUrl || 'http://localhost:5000',
      theme: options.theme || 'light',
      autoRefresh: options.autoRefresh !== false,
      refreshInterval: options.refreshInterval || 60000,
      showCharts: options.showCharts !== false,
      ...options
    };
    
    this.charts = {};
    this.refreshTimer = null;
    this.init();
  }

  init() {
    this.loadDependencies().then(() => {
      this.render();
      this.loadData();
      if (this.options.autoRefresh) this.startAutoRefresh();
    });
  }

  async loadDependencies() {
    if (!window.Chart) {
      await this.loadScript('https://cdn.jsdelivr.net/npm/chart.js');
    }
  }

  loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  render() {
    const container = document.getElementById(this.options.containerId);
    if (!container) {
      console.error(`Container ${this.options.containerId} not found`);
      return;
    }

    container.innerHTML = `
      <div class="instareview-widget ${this.options.theme}">
        <style>
          .instareview-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
          .instareview-widget.light { background: #fff; color: #333; }
          .instareview-widget.dark { background: #1a1a1a; color: #fff; }
          .ir-header { padding: 16px; border-bottom: 1px solid #e5e5e5; display: flex; justify-content: between; align-items: center; }
          .ir-title { font-size: 18px; font-weight: 600; margin: 0; }
          .ir-status { font-size: 12px; display: flex; align-items: center; gap: 8px; }
          .ir-indicator { width: 8px; height: 8px; border-radius: 50%; background: #10b981; }
          .ir-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; padding: 16px; }
          .ir-metric { text-align: center; padding: 16px; border-radius: 8px; background: #f8f9fa; }
          .ir-metric-value { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
          .ir-metric-label { font-size: 12px; color: #666; }
          .ir-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px; }
          .ir-chart { height: 200px; }
          .ir-themes { padding: 16px; }
          .ir-theme-tag { display: inline-block; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 11px; background: #e3f2fd; color: #1976d2; }
          .ir-theme-tag.negative { background: #ffebee; color: #d32f2f; }
        </style>
        
        <div class="ir-header">
          <h3 class="ir-title">Analytics Dashboard</h3>
          <div class="ir-status">
            <span class="ir-indicator" id="ir-indicator"></span>
            <span id="ir-status-text">Loading...</span>
          </div>
        </div>
        
        <div class="ir-metrics">
          <div class="ir-metric">
            <div class="ir-metric-value" id="ir-total">0</div>
            <div class="ir-metric-label">Total Reviews</div>
          </div>
          <div class="ir-metric">
            <div class="ir-metric-value" style="color: #10b981;" id="ir-positive">0%</div>
            <div class="ir-metric-label">Positive</div>
          </div>
          <div class="ir-metric">
            <div class="ir-metric-value" style="color: #f59e0b;" id="ir-neutral">0%</div>
            <div class="ir-metric-label">Neutral</div>
          </div>
          <div class="ir-metric">
            <div class="ir-metric-value" style="color: #ef4444;" id="ir-negative">0%</div>
            <div class="ir-metric-label">Negative</div>
          </div>
        </div>
        
        ${this.options.showCharts ? `
        <div class="ir-charts">
          <div class="ir-chart">
            <canvas id="ir-sentiment-chart"></canvas>
          </div>
          <div class="ir-chart">
            <canvas id="ir-ratings-chart"></canvas>
          </div>
        </div>
        ` : ''}
        
        <div class="ir-themes">
          <div style="margin-bottom: 12px;">
            <strong>Positive Themes:</strong>
            <div id="ir-positive-themes"></div>
          </div>
          <div>
            <strong>Areas for Improvement:</strong>
            <div id="ir-negative-themes"></div>
          </div>
        </div>
      </div>
    `;

    if (this.options.showCharts) {
      this.initCharts();
    }
  }

  initCharts() {
    // Sentiment Chart
    this.charts.sentiment = new Chart(document.getElementById('ir-sentiment-chart'), {
      type: 'doughnut',
      data: {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [{
          data: [0, 0, 0],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { fontSize: 10 } } }
      }
    });

    // Ratings Chart
    this.charts.ratings = new Chart(document.getElementById('ir-ratings-chart'), {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Rating',
          data: [],
          backgroundColor: '#3b82f6',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, max: 5 } },
        plugins: { legend: { display: false } }
      }
    });
  }

  async loadData() {
    try {
      document.getElementById('ir-status-text').textContent = 'Loading...';
      
      const response = await fetch(`${this.options.apiUrl}/api/data`);
      const data = await response.json();
      
      if (data.error) throw new Error(data.error);
      
      this.updateWidget(data);
      document.getElementById('ir-status-text').textContent = 'Live';
      
    } catch (error) {
      console.error('Widget update failed:', error);
      document.getElementById('ir-status-text').textContent = 'Error';
      document.getElementById('ir-indicator').style.background = '#ef4444';
    }
  }

  updateWidget(data) {
    const analytics = this.generateAnalytics(data);
    const total = analytics.totalRecords;
    const positive = analytics.sentimentBreakdown.Positive || 0;
    const neutral = analytics.sentimentBreakdown.Neutral || 0;
    const negative = analytics.sentimentBreakdown.Negative || 0;

    // Update metrics
    document.getElementById('ir-total').textContent = total;
    document.getElementById('ir-positive').textContent = total > 0 ? Math.round((positive/total)*100) + '%' : '0%';
    document.getElementById('ir-neutral').textContent = total > 0 ? Math.round((neutral/total)*100) + '%' : '0%';
    document.getElementById('ir-negative').textContent = total > 0 ? Math.round((negative/total)*100) + '%' : '0%';

    // Update themes
    document.getElementById('ir-positive-themes').innerHTML = 
      analytics.positiveThemes.slice(0, 5).map(theme => 
        `<span class="ir-theme-tag">${theme}</span>`).join('');
    
    document.getElementById('ir-negative-themes').innerHTML = 
      analytics.negativeThemes.slice(0, 5).map(theme => 
        `<span class="ir-theme-tag negative">${theme}</span>`).join('');

    // Update charts
    if (this.options.showCharts && this.charts.sentiment) {
      this.charts.sentiment.data.datasets[0].data = [positive, neutral, negative];
      this.charts.sentiment.update();

      const ratings = Object.entries(analytics.averageRatings);
      this.charts.ratings.data.labels = ratings.map(([q]) => q.substring(0, 10) + '...');
      this.charts.ratings.data.datasets[0].data = ratings.map(([, r]) => parseFloat(r));
      this.charts.ratings.update();
    }
  }

  generateAnalytics(reportData) {
    const safeGet = (obj, path, defaultValue = []) => {
      try {
        return path.split('.').reduce((o, p) => o && o[p], obj) || defaultValue;
      } catch {
        return defaultValue;
      }
    };
    
    return {
      totalRecords: safeGet(reportData, 'overall_stats.total_feedback', 0),
      sentimentBreakdown: safeGet(reportData, 'audio_metrics.sentiment_distribution', {}),
      averageRatings: safeGet(reportData, 'survey_metrics.question_averages', {}),
      positiveThemes: safeGet(reportData, 'audio_metrics.positive_themes', []),
      negativeThemes: safeGet(reportData, 'audio_metrics.negative_themes', [])
    };
  }

  startAutoRefresh() {
    this.refreshTimer = setInterval(() => this.loadData(), this.options.refreshInterval);
  }

  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  destroy() {
    this.stopAutoRefresh();
    Object.values(this.charts).forEach(chart => chart.destroy());
    const container = document.getElementById(this.options.containerId);
    if (container) container.innerHTML = '';
  }
}

// Auto-initialize from script tag data attributes
document.addEventListener('DOMContentLoaded', () => {
  const scripts = document.querySelectorAll('script[src*="dashboard-widget.js"]');
  scripts.forEach(script => {
    const options = {
      containerId: script.dataset.containerId,
      companyId: script.dataset.companyId,
      apiUrl: script.dataset.apiUrl,
      theme: script.dataset.theme,
      autoRefresh: script.dataset.autoRefresh !== 'false',
      refreshInterval: parseInt(script.dataset.refreshInterval) || 60000,
      showCharts: script.dataset.showCharts !== 'false'
    };
    
    if (options.containerId) {
      new InstaReviewWidget(options);
    }
  });
});

window.InstaReviewWidget = InstaReviewWidget;