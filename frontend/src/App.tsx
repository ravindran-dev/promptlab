import { useState, useEffect } from 'react';
import { 
  Play, 
  Cpu, 
  Award, 
  Edit3, 
  Activity, 
  RefreshCw, 
  AlertCircle, 
  Clock, 
  Coins, 
  Zap, 
  Database,
  Download
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer
} from 'recharts';

const BACKEND_URL = 'http://localhost:8000';

// Mock Data for local fallback when backend is unavailable
const MOCK_LEADERBOARD = [
  { version: 'v3', average_score: 91.7, average_latency: 1820.0, average_tokens: 1850.0, coverage_score: 95.0, hallucination_score: 98.0, runs_count: 42 },
  { version: 'v2', average_score: 82.4, average_latency: 1250.0, average_tokens: 1210.0, coverage_score: 78.0, hallucination_score: 86.0, runs_count: 38 },
  { version: 'v1', average_score: 64.2, average_latency: 820.0, average_tokens: 850.0, coverage_score: 55.5, hallucination_score: 68.0, runs_count: 35 }
];

const MOCK_TRENDS = {
  v1: [
    { timestamp: '09:00', avg_score: 62.1, avg_coverage: 52.0, avg_hallucination: 65.0, avg_latency: 800.0, avg_tokens: 820.0 },
    { timestamp: '11:00', avg_score: 63.5, avg_coverage: 54.0, avg_hallucination: 67.0, avg_latency: 810.0, avg_tokens: 840.0 },
    { timestamp: '13:00', avg_score: 64.2, avg_coverage: 55.5, avg_hallucination: 68.0, avg_latency: 820.0, avg_tokens: 850.0 }
  ],
  v2: [
    { timestamp: '09:00', avg_score: 80.5, avg_coverage: 76.0, avg_hallucination: 84.0, avg_latency: 1200.0, avg_tokens: 1180.0 },
    { timestamp: '11:00', avg_score: 81.8, avg_coverage: 77.0, avg_hallucination: 85.0, avg_latency: 1230.0, avg_tokens: 1200.0 },
    { timestamp: '13:00', avg_score: 82.4, avg_coverage: 78.0, avg_hallucination: 86.0, avg_latency: 1250.0, avg_tokens: 1210.0 }
  ],
  v3: [
    { timestamp: '09:00', avg_score: 89.2, avg_coverage: 92.0, avg_hallucination: 96.0, avg_latency: 1750.0, avg_tokens: 1800.0 },
    { timestamp: '11:00', avg_score: 90.5, avg_coverage: 94.0, avg_hallucination: 97.0, avg_latency: 1800.0, avg_tokens: 1820.0 },
    { timestamp: '13:00', avg_score: 91.7, avg_coverage: 95.0, avg_hallucination: 98.0, avg_latency: 1820.0, avg_tokens: 1850.0 }
  ]
};

const MOCK_BENCHMARKS = [
  { id: 'small_1_dark_mode', category: 'small_features', problem: 'Users complain about eye strain when using the dashboard at night.', solution: 'Implement a client-side dark mode toggle in the header.', goals: 'Allow users to toggle dark mode instantly. Persist preference across sessions. Align UI colors with accessible contrast guidelines.', template: '## 1. Feature Description\n## 2. UI/UX Behaviors\n## 3. Storage & State Management' },
  { id: 'medium_1_shopping_cart', category: 'medium_features', problem: 'Customers cannot save items for purchase, forcing them to buy items one-by-one.', solution: 'Develop a persistent shopping cart service with quantity adjustments and summary calculations.', goals: 'Maintain cart items in local state and sync to DB for logged-in users. Calculate taxes and discounts. Limit item quantity based on stock.', template: '## 1. Functional Requirements\n## 2. Database Model Draft\n## 3. API Routes & Cart Logic\n## 4. Checkout CTA Triggers' },
  { id: 'large_1_checkout_pipeline', category: 'large_flows', problem: 'High checkout abandonment rate due to complex pages, lack of guest checkout, and vague payment flows.', solution: 'Design a structured, linear 3-step checkout flow: Shipping Info, Billing & Payment, and Order Review.', goals: 'Support Guest Checkout. Verify shipping addresses using third-party APIs. Process credit cards via Stripe securely.', template: '## 1. Flow Diagram Description\n## 2. Detailed Checkout Steps\n## 3. Error Recovery & Card Validation\n## 4. API Endpoints and Payloads\n## 5. Security & PCI Compliance' }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'leaderboard' | 'benchmark' | 'comparison' | 'playground' | 'registry'>('leaderboard');
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [stats, setStats] = useState<any>({ leaderboard: MOCK_LEADERBOARD, trends: MOCK_TRENDS, total_runs: 115, avg_latency: 1290.0, avg_tokens: 1300.0 });
  const [loading, setLoading] = useState<boolean>(false);
  
  // Benchmark state
  const [benchmarkCases, setBenchmarkCases] = useState<any[]>(MOCK_BENCHMARKS);
  const [selectedVersions, setSelectedVersions] = useState<string[]>(['v1', 'v2', 'v3']);
  const [benchmarkResult, setBenchmarkResult] = useState<any | null>(null);
  
  // Playground state
  const [problem, setProblem] = useState('Users miss key notifications because they only appear in the app.');
  const [solution, setSolution] = useState('Create an automated email and SMS notification dispatch service.');
  const [goals, setGoals] = useState('Deliver notifications in under 2 seconds. Provide opt-out preferences. Log notification delivery states.');
  const [template, setTemplate] = useState('## 1. Product Overview\n## 2. Notification Channels\n## 3. Opt-out Preferences & Compliance\n## 4. API Routes');
  const [selectedVersion, setSelectedVersion] = useState('v3');
  const [generatedPrd, setGeneratedPrd] = useState<string>('');
  const [genStats, setGenStats] = useState<any | null>(null);

  // Registry state
  const [prompts, setPrompts] = useState<any[]>([]);
  const [editingVersion, setEditingVersion] = useState<string>('v3');
  const [promptContent, setPromptContent] = useState<string>('');

  // Check API Connection & Fetch Stats
  const checkConnection = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/`);
      if (res.ok) {
        setBackendOnline(true);
        fetchStats();
        fetchCases();
        fetchPrompts();
      } else {
        setBackendOnline(false);
      }
    } catch {
      setBackendOnline(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/metrics/dashboard`);
      if (res.ok) {
        const data = await res.json();
        if (data.leaderboard && data.leaderboard.length > 0) {
          setStats(data);
        }
      }
    } catch (e) {
      console.error("Error fetching stats:", e);
    }
  };

  const fetchCases = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/benchmark/cases`);
      if (res.ok) {
        const data = await res.json();
        setBenchmarkCases(data);
      }
    } catch (e) {
      console.error("Error fetching benchmark cases:", e);
    }
  };

  const fetchPrompts = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/prompts`);
      if (res.ok) {
        const data = await res.json();
        setPrompts(data);
        const active = data.find((p: any) => p.version === editingVersion) || data[0];
        if (active) {
          setPromptContent(active.content);
        }
      }
    } catch (e) {
      console.error("Error fetching prompts:", e);
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (backendOnline) {
      const current = prompts.find(p => p.version === editingVersion);
      if (current) {
        setPromptContent(current.content);
      } else {
        // Fetch specific
        fetch(`${BACKEND_URL}/api/prompts/${editingVersion}`)
          .then(res => { if (res.ok) return res.json(); })
          .then(data => { if (data) setPromptContent(data.content); });
      }
    }
  }, [editingVersion, prompts, backendOnline]);

  const handleGenerate = async () => {
    setLoading(true);
    setGeneratedPrd('');
    setGenStats(null);
    try {
      if (backendOnline) {
        const res = await fetch(`${BACKEND_URL}/api/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ problem, solution, goals, template, prompt_version: selectedVersion })
        });
        if (res.ok) {
          const data = await res.json();
          setGeneratedPrd(data.prd);
          setGenStats({
            tokens: data.tokens,
            latency_ms: data.latency_ms,
            model: data.model,
            scores: data.scores
          });
          fetchStats(); // Update dashboard
        } else {
          let errorDetail = `Backend returned HTTP ${res.status}.`;
          try {
            const errorBody = await res.json();
            errorDetail = errorBody.detail || JSON.stringify(errorBody);
          } catch {
            errorDetail = await res.text();
          }
          setGeneratedPrd(`Error generating PRD. ${errorDetail}`);
        }
      } else {
        // Frontend mock generation
        setTimeout(() => {
          setGeneratedPrd(`# Product Requirement Document (MOCK GENERATED)

## 1. Product Overview
This document specifies the notification system handling problem: "${problem}".

## 2. Core Requirements
- Support dispatch over Email and SMS.
- Keep latency below 2 seconds (currently simulated).
- Target Goals: ${goals}.

## 3. UI Flow Mockup
- Dashboard toggle preferences panel showing checkboxes.
- Subscription status banners.

*Note: Connect the FastAPI backend to generate actual AI-driven PRDs.*`);
          setGenStats({
            tokens: 1250,
            latency_ms: 1450,
            model: 'mock-model-gpt-4o',
            scores: {
              coverage: 85,
              hallucination: 92,
              design: 80,
              engineering: 75,
              qa: 70,
              prototype: 80,
              repetition: 95,
              format: 90,
              final_score: 82.5
            }
          });
          setLoading(false);
        }, 1500);
        return;
      }
    } catch (e) {
      setGeneratedPrd(`Failed to connect to backend: ${e}`);
    }
    setLoading(false);
  };

  const escapeHtml = (value: string) =>
    value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');

  const markdownToPrintableHtml = (markdown: string) =>
    escapeHtml(markdown)
      .split('\n')
      .map((line) => {
        if (line.startsWith('### ')) return `<h3>${line.slice(4)}</h3>`;
        if (line.startsWith('## ')) return `<h2>${line.slice(3)}</h2>`;
        if (line.startsWith('# ')) return `<h1>${line.slice(2)}</h1>`;
        if (line.startsWith('- ') || line.startsWith('* ')) return `<p class="bullet">${line.slice(2)}</p>`;
        if (line.trim() === '') return '<br />';
        return `<p>${line}</p>`;
      })
      .join('\n');

  const buildPdfHtml = () => {
    const score = genStats?.scores?.final_score;
    return `
      <!doctype html>
      <html>
        <head>
          <title>PromptLab PRD Export</title>
          <style>
            @page { margin: 18mm; }
            body { color: #111827; font-family: Arial, sans-serif; line-height: 1.5; }
            header { border-bottom: 1px solid #d1d5db; margin-bottom: 24px; padding-bottom: 12px; }
            .meta { color: #4b5563; font-size: 12px; margin-top: 6px; }
            h1 { font-size: 24px; margin: 18px 0 10px; }
            h2 { font-size: 18px; border-bottom: 1px solid #e5e7eb; margin: 18px 0 8px; padding-bottom: 4px; }
            h3 { font-size: 15px; margin: 14px 0 6px; }
            p { font-size: 12px; margin: 5px 0; }
            .bullet::before { content: "• "; }
          </style>
        </head>
        <body>
          <header>
            <h1>PromptLab PRD Export</h1>
            <div class="meta">
              Model: ${escapeHtml(genStats?.model || 'unknown')} |
              Tokens: ${escapeHtml(String(genStats?.tokens ?? 'n/a'))} |
              Latency: ${escapeHtml(String(genStats?.latency_ms ?? 'n/a'))}ms |
              Score: ${escapeHtml(score === undefined ? 'n/a' : score.toFixed(1))}
            </div>
          </header>
          <main>${markdownToPrintableHtml(generatedPrd)}</main>
          <script>
            window.onload = () => {
              window.focus();
              window.print();
            };
          </script>
        </body>
      </html>
    `;
  };

  const handleDownloadPdf = () => {
    if (!generatedPrd.trim()) return;

    const html = buildPdfHtml();
    const printable = window.open('', '_blank', 'noopener,noreferrer,width=900,height=700');
    if (printable) {
      printable.document.write(html);
      printable.document.close();
      return;
    }

    const frame = document.createElement('iframe');
    frame.style.position = 'fixed';
    frame.style.right = '0';
    frame.style.bottom = '0';
    frame.style.width = '0';
    frame.style.height = '0';
    frame.style.border = '0';
    document.body.appendChild(frame);

    const doc = frame.contentWindow?.document;
    if (!doc) {
      alert('Unable to create PDF preview. Please allow popups to export the output.');
      frame.remove();
      return;
    }

    doc.open();
    doc.write(html);
    doc.close();

    setTimeout(() => {
      frame.contentWindow?.focus();
      frame.contentWindow?.print();
      frame.remove();
    }, 250);
  };

  const handleRunBenchmark = async () => {
    setLoading(true);
    setBenchmarkResult(null);
    try {
      if (backendOnline) {
        const res = await fetch(`${BACKEND_URL}/api/benchmark/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            prompt_versions: selectedVersions,
            limit: 3 // Run 3 cases synchronously in UI to prevent HTTP timeouts
          })
        });
        if (res.ok) {
          const data = await res.json();
          setBenchmarkResult(data);
          fetchStats();
        } else {
          alert("Error running benchmark suite.");
        }
      } else {
        // Mock run
        setTimeout(() => {
          setBenchmarkResult({
            winner: 'v3',
            summaries: {
              v1: { prompt_version: 'v1', average_score: 65.4, average_latency: 850, average_tokens: 880, coverage: 56.0, hallucination: 30.0, cases_run: 3, results: [] },
              v2: { prompt_version: 'v2', average_score: 83.1, average_latency: 1290, average_tokens: 1230, coverage: 79.5, hallucination: 12.0, cases_run: 3, results: [] },
              v3: { prompt_version: 'v3', average_score: 92.5, average_latency: 1850, average_tokens: 1820, coverage: 96.0, hallucination: 2.0, cases_run: 3, results: [] }
            }
          });
          setLoading(false);
        }, 3000);
        return;
      }
    } catch (e) {
      alert(`Failed to run benchmark suite: ${e}`);
    }
    setLoading(false);
  };

  const handleSavePrompt = async () => {
    if (!backendOnline) {
      alert("Backend is offline. Cannot save changes to prompt registry.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/prompts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          version: editingVersion,
          content: promptContent,
          description: `Updated via PromptLab Dashboard Editor`
        })
      });
      if (res.ok) {
        alert(`Prompt version ${editingVersion} successfully updated in database!`);
        fetchPrompts();
      } else {
        alert("Failed to save prompt registry change.");
      }
    } catch (e) {
      alert(`Error updating prompt registry: ${e}`);
    }
    setLoading(false);
  };

  // Convert trends data for plotting
  const prepareChartData = () => {
    const dataMap: { [key: string]: any } = {};
    Object.keys(stats.trends).forEach(version => {
      stats.trends[version].forEach((pt: any) => {
        if (!dataMap[pt.timestamp]) {
          dataMap[pt.timestamp] = { timestamp: pt.timestamp };
        }
        dataMap[pt.timestamp][`${version}_score`] = pt.avg_score;
        dataMap[pt.timestamp][`${version}_coverage`] = pt.avg_coverage;
        dataMap[pt.timestamp][`${version}_hallucination`] = 100 - pt.avg_hallucination; // Hallucination count / offset
      });
    });
    return Object.values(dataMap).sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col">
      {/* Upper sleek navbar */}
      <header className="border-b border-darkborder bg-[#0B0F19]/90 sticky top-0 z-50 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center font-bold text-white shadow-lg shadow-brand-500/20 text-lg">
            PL
          </div>
          <div>
            <h1 className="font-bold text-xl tracking-tight text-white flex items-center gap-2">
              PromptLab <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-mono">ProductOS</span>
            </h1>
            <p className="text-xs text-gray-400">Continuous Prompt Optimization & Benchmarking</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs bg-darkcard border border-darkborder px-3 py-1.5 rounded-lg">
            <span className={`h-2.5 w-2.5 rounded-full ${backendOnline ? 'bg-emerald-500 glow-pulse' : 'bg-red-500'}`} />
            <span className="font-mono text-gray-300">API Status: {backendOnline ? 'ONLINE (Port 8000)' : 'OFFLINE (Mocking Enabled)'}</span>
          </div>
          <button 
            onClick={checkConnection}
            className="p-1.5 rounded-lg bg-darkcard border border-darkborder hover:bg-gray-800 transition-colors"
            title="Refresh connection status"
          >
            <RefreshCw className="h-4 w-4 text-gray-400" />
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        
        {/* Statistics Cards */}
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass p-5 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">TOTAL EVALUATIONS</p>
              <h3 className="text-2xl font-bold mt-1 text-white">{stats.total_runs}</h3>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1 mt-1">
                <Activity className="h-3 w-3" /> Runs logged in DB
              </p>
            </div>
            <div className="p-3 bg-brand-500/10 text-brand-500 rounded-xl">
              <Database className="h-6 w-6" />
            </div>
          </div>

          <div className="glass p-5 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">LEADERBOARD WINNER</p>
              <h3 className="text-2xl font-bold mt-1 text-emerald-400">
                {stats.leaderboard[0] ? stats.leaderboard[0].version.toUpperCase() : 'N/A'}
              </h3>
              <p className="text-[10px] text-gray-400 mt-1">
                Score: {stats.leaderboard[0] ? stats.leaderboard[0].average_score : '0.0'} / 100
              </p>
            </div>
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
              <Award className="h-6 w-6" />
            </div>
          </div>

          <div className="glass p-5 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">AVG LLM LATENCY</p>
              <h3 className="text-2xl font-bold mt-1 text-white">
                {stats.avg_latency.toFixed(0)} ms
              </h3>
              <p className="text-[10px] text-blue-400 flex items-center gap-1 mt-1">
                <Clock className="h-3 w-3" /> Pipeline generation speed
              </p>
            </div>
            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-xl">
              <Zap className="h-6 w-6" />
            </div>
          </div>

          <div className="glass p-5 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 font-medium">AVG TOKEN USAGE</p>
              <h3 className="text-2xl font-bold mt-1 text-white">
                {stats.avg_tokens.toFixed(0)}
              </h3>
              <p className="text-[10px] text-indigo-400 flex items-center gap-1 mt-1">
                <Coins className="h-3 w-3" /> Input + Output tokens
              </p>
            </div>
            <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl">
              <Cpu className="h-6 w-6" />
            </div>
          </div>
        </section>

        {/* Navigation Tabs */}
        <nav className="flex border-b border-darkborder gap-2 bg-darkcard/50 p-1.5 rounded-xl border">
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'leaderboard' ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/10' : 'text-gray-400 hover:text-white hover:bg-gray-800/40'}`}
          >
            <Award className="h-4 w-4" /> Prompt Leaderboard
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'benchmark' ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/10' : 'text-gray-400 hover:text-white hover:bg-gray-800/40'}`}
          >
            <Activity className="h-4 w-4" /> Benchmark Suites
          </button>
          <button
            onClick={() => setActiveTab('playground')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'playground' ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/10' : 'text-gray-400 hover:text-white hover:bg-gray-800/40'}`}
          >
            <Play className="h-4 w-4" /> PRD Playground
          </button>
          <button
            onClick={() => setActiveTab('registry')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'registry' ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/10' : 'text-gray-400 hover:text-white hover:bg-gray-800/40'}`}
          >
            <Edit3 className="h-4 w-4" /> Prompt Registry
          </button>
        </nav>

        {/* Tab View Contents */}
        <section className="flex-1">
          {activeTab === 'leaderboard' && (
            <div className="flex flex-col gap-6">
              
              {/* Leaderboard Table & Trend Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Leaderboard Rankings */}
                <div className="glass p-6 rounded-2xl lg:col-span-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Prompt Leaderboard</h3>
                    <div className="flex flex-col gap-3">
                      {stats.leaderboard.map((item: any, idx: number) => (
                        <div key={item.version} className="bg-darkcard border border-darkborder p-4 rounded-xl flex items-center justify-between hover:border-gray-600 transition-colors">
                          <div className="flex items-center gap-3">
                            <span className="h-6 w-6 rounded bg-gray-800 border border-gray-700 flex items-center justify-center font-mono text-xs font-semibold">
                              {idx + 1}
                            </span>
                            <div>
                              <h4 className="font-bold text-white text-sm">Prompt {item.version.toUpperCase()}</h4>
                              <p className="text-[10px] text-gray-400 font-mono mt-0.5">Runs: {item.runs_count} | Latency: {item.average_latency.toFixed(0)}ms</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="text-lg font-bold text-brand-500 font-mono">{item.average_score.toFixed(1)}</span>
                            <p className="text-[10px] text-gray-400">Avg Quality</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="mt-6 border-t border-darkborder pt-4 text-xs text-gray-400">
                    💡 <span className="font-semibold text-gray-300">Prompt V3</span> currently outperforms V1 by <span className="text-brand-500 font-bold">{(stats.leaderboard[0] && stats.leaderboard[2]) ? (stats.leaderboard[0].average_score - stats.leaderboard[2].average_score).toFixed(1) : '27.5'}%</span> on coverage and factual correctness.
                  </div>
                </div>

                {/* Score Chart Trends */}
                <div className="glass p-6 rounded-2xl lg:col-span-2 flex flex-col">
                  <h3 className="text-lg font-semibold text-white mb-2">Quality Performance Trends</h3>
                  <p className="text-xs text-gray-400 mb-6">Historical tracker charting the aggregate final scores of prompt versions.</p>
                  
                  <div className="flex-1 min-h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={prepareChartData()} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorV3" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorV2" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorV1" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2}/>
                            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1F293D" />
                        <XAxis dataKey="timestamp" stroke="#9ca3af" fontSize={11} />
                        <YAxis domain={[50, 100]} stroke="#9ca3af" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#161F30', borderColor: '#1F293D', color: '#fff' }} />
                        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                        <Area name="Prompt V3" type="monotone" dataKey="v3_score" stroke="#10b981" fillOpacity={1} fill="url(#colorV3)" strokeWidth={2} />
                        <Area name="Prompt V2" type="monotone" dataKey="v2_score" stroke="#3b82f6" fillOpacity={1} fill="url(#colorV2)" strokeWidth={2} />
                        <Area name="Prompt V1" type="monotone" dataKey="v1_score" stroke="#f59e0b" fillOpacity={1} fill="url(#colorV1)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

              </div>

              {/* Detailed Breakdown Charts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Metrics comparison charts */}
                <div className="glass p-6 rounded-2xl flex flex-col">
                  <h3 className="text-lg font-semibold text-white mb-2">Requirement Coverage & Hallucination Resistance</h3>
                  <p className="text-xs text-gray-400 mb-6">Comparative view of scores for the two primary weighted evaluation metrics (20% each).</p>
                  
                  <div className="flex-1 min-h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stats.leaderboard} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1F293D" />
                        <XAxis dataKey="version" stroke="#9ca3af" fontSize={11} tickFormatter={(val) => val.toUpperCase()} />
                        <YAxis domain={[0, 100]} stroke="#9ca3af" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#161F30', borderColor: '#1F293D', color: '#fff' }} />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Bar name="Coverage Score" dataKey="coverage_score" fill="#10b981" radius={[4, 4, 0, 0]} />
                        <Bar name="Hallucination Resistance" dataKey="hallucination_score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Token and Latency comparisons */}
                <div className="glass p-6 rounded-2xl flex flex-col">
                  <h3 className="text-lg font-semibold text-white mb-2">Cost & Performance Tradeoff</h3>
                  <p className="text-xs text-gray-400 mb-6">Analyzing execution speed (latency) vs cost (avg token usage) per prompt version.</p>
                  
                  <div className="flex-1 min-h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stats.leaderboard} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1F293D" />
                        <XAxis dataKey="version" stroke="#9ca3af" fontSize={11} tickFormatter={(val) => val.toUpperCase()} />
                        <YAxis yAxisId="left" orientation="left" stroke="#3b82f6" fontSize={11} label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft', style: { fill: '#3b82f6' } }} />
                        <YAxis yAxisId="right" orientation="right" stroke="#818cf8" fontSize={11} label={{ value: 'Tokens', angle: 90, position: 'insideRight', style: { fill: '#818cf8' } }} />
                        <Tooltip contentStyle={{ backgroundColor: '#161F30', borderColor: '#1F293D', color: '#fff' }} />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        <Bar yAxisId="left" name="Avg Latency (ms)" dataKey="average_latency" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        <Bar yAxisId="right" name="Avg Tokens" dataKey="average_tokens" fill="#818cf8" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

              </div>

            </div>
          )}

          {activeTab === 'benchmark' && (
            <div className="glass p-6 rounded-2xl flex flex-col gap-6">
              <div className="flex items-center justify-between border-b border-darkborder pb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Benchmark Suite Runner</h3>
                  <p className="text-xs text-gray-400">Evaluate prompt versions across a structured set of 30 test cases stored in the registry.</p>
                </div>
                <button
                  onClick={handleRunBenchmark}
                  disabled={loading}
                  className={`flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium px-5 py-2.5 rounded-xl text-sm transition-all shadow-lg ${loading ? 'shadow-none' : 'shadow-brand-500/20 hover:scale-[1.02]'}`}
                >
                  <Play className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Executing Suite...' : 'Run Benchmark (Limit 3 Cases)'}
                </button>
              </div>

              {/* Benchmarking selection panel */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Selectors */}
                <div className="bg-darkcard border border-darkborder p-5 rounded-2xl flex flex-col gap-4">
                  <h4 className="font-semibold text-white text-sm">Suite Configuration</h4>
                  
                  <div>
                    <label className="text-xs text-gray-400 block mb-2">Prompt Versions to Test</label>
                    <div className="flex flex-col gap-2">
                      {['v1', 'v2', 'v3'].map(v => (
                        <label key={v} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                          <input 
                            type="checkbox"
                            checked={selectedVersions.includes(v)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedVersions([...selectedVersions, v]);
                              } else {
                                setSelectedVersions(selectedVersions.filter(x => x !== v));
                              }
                            }}
                            className="rounded bg-gray-800 border-gray-700 text-brand-600 focus:ring-brand-500 focus:ring-offset-darkcard"
                          />
                          Prompt {v.toUpperCase()}
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="border-t border-darkborder pt-3">
                    <span className="text-xs text-gray-400 block mb-2">Available Cases ({benchmarkCases.length})</span>
                    <div className="max-h-[220px] overflow-y-auto pr-2 flex flex-col gap-1.5 text-xs text-gray-300 font-mono">
                      {benchmarkCases.map(bc => (
                        <div key={bc.id} className="p-2 bg-darkbg rounded border border-darkborder flex items-center justify-between">
                          <span className="truncate max-w-[170px]" title={bc.id}>{bc.id}</span>
                          <span className="text-[10px] text-gray-500 px-1 bg-gray-800 rounded">{bc.category.split('_')[0]}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Benchmark results report output */}
                <div className="md:col-span-2 bg-darkcard border border-darkborder p-5 rounded-2xl flex flex-col justify-between min-h-[350px]">
                  
                  {benchmarkResult ? (
                    <div className="flex flex-col gap-5 flex-1 justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-4 border-b border-darkborder pb-2">
                          <h4 className="font-semibold text-white text-sm">Comparative Run Summary</h4>
                          <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded font-mono font-bold">
                            Winner: Prompt {benchmarkResult.winner.toUpperCase()}
                          </span>
                        </div>

                        {/* Leaderboard layout matches the terminal format requested */}
                        <div className="grid grid-cols-3 gap-4 mb-4 text-center">
                          {Object.values(benchmarkResult.summaries).map((sum: any) => (
                            <div key={sum.prompt_version} className="bg-darkbg border border-darkborder p-3 rounded-xl">
                              <span className="text-xs text-gray-400">Prompt {sum.prompt_version.toUpperCase()}</span>
                              <div className="text-lg font-bold text-white mt-1">{sum.average_score.toFixed(1)}</div>
                              <span className="text-[9px] text-gray-500 font-mono">Latency: {sum.average_latency.toFixed(0)}ms</span>
                            </div>
                          ))}
                        </div>

                        <div className="grid grid-cols-2 gap-6 text-sm text-gray-300">
                          <div>
                            <span className="text-xs font-semibold text-gray-400 block mb-2">Requirement Coverage:</span>
                            <div className="flex flex-col gap-1.5 font-mono text-xs">
                              {Object.values(benchmarkResult.summaries).map((sum: any) => (
                                <div key={sum.prompt_version} className="flex justify-between p-1 border-b border-darkborder">
                                  <span>{sum.prompt_version.toUpperCase()}</span>
                                  <span className="font-bold text-emerald-400">{sum.coverage}%</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div>
                            <span className="text-xs font-semibold text-gray-400 block mb-2">Hallucinations (100 - Resistance):</span>
                            <div className="flex flex-col gap-1.5 font-mono text-xs">
                              {Object.values(benchmarkResult.summaries).map((sum: any) => (
                                <div key={sum.prompt_version} className="flex justify-between p-1 border-b border-darkborder">
                                  <span>{sum.prompt_version.toUpperCase()}</span>
                                  <span className="font-bold text-red-400">{Math.max(0, 100 - sum.hallucination).toFixed(1)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="text-[11px] text-gray-500 bg-darkbg p-3 border border-darkborder rounded-lg font-mono">
                        Console output generated. Run <code className="text-brand-500 font-bold bg-black/30 px-1 py-0.5 rounded">npm run benchmark</code> to view detailed metrics matrix output directly in your CLI shell.
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                      <AlertCircle className="h-10 w-10 text-gray-500 mb-3" />
                      <h4 className="font-semibold text-white mb-1">No Benchmark Result Load</h4>
                      <p className="text-xs text-gray-400 max-w-sm">Click "Run Benchmark" above to run the active prompt versions against the seed cases and see comparative quality rankings.</p>
                    </div>
                  )}

                </div>

              </div>

            </div>
          )}

          {activeTab === 'playground' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Inputs Form */}
              <div className="glass p-6 rounded-2xl flex flex-col gap-4">
                <h3 className="text-lg font-semibold text-white border-b border-darkborder pb-3">PRD Sandbox Inputs</h3>
                
                <div className="flex flex-col gap-3">
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Prompt Version</label>
                    <select
                      value={selectedVersion}
                      onChange={(e) => setSelectedVersion(e.target.value)}
                      className="w-full bg-darkcard border border-darkborder rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
                    >
                      <option value="v1">Prompt V1 (Basic)</option>
                      <option value="v2">Prompt V2 (Structured)</option>
                      <option value="v3">Prompt V3 (Principal PM/Fast)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Core Problem</label>
                    <textarea
                      rows={2}
                      value={problem}
                      onChange={(e) => setProblem(e.target.value)}
                      className="w-full bg-darkcard border border-darkborder rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500 resize-none font-sans"
                      placeholder="What is the problem statement?"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Proposed Solution</label>
                    <textarea
                      rows={2}
                      value={solution}
                      onChange={(e) => setSolution(e.target.value)}
                      className="w-full bg-darkcard border border-darkborder rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500 resize-none font-sans"
                      placeholder="What is the solution?"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Strategic Goals</label>
                    <textarea
                      rows={2}
                      value={goals}
                      onChange={(e) => setGoals(e.target.value)}
                      className="w-full bg-darkcard border border-darkborder rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500 resize-none font-sans"
                      placeholder="What are the goals?"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Markdown Structure Template</label>
                    <textarea
                      rows={4}
                      value={template}
                      onChange={(e) => setTemplate(e.target.value)}
                      className="w-full bg-darkcard border border-darkborder rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500 font-mono resize-y"
                      placeholder="Structure headings..."
                    />
                  </div>
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className={`w-full mt-2 flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-all shadow-lg ${loading ? 'shadow-none' : 'shadow-brand-500/20'}`}
                >
                  <Play className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  {loading ? 'Invoking LangGraph Workflow...' : 'Generate PRD & Evaluate'}
                </button>
              </div>

              {/* Outputs Displays */}
              <div className="glass p-6 rounded-2xl flex flex-col justify-between min-h-[500px]">
                <div className="flex-1 flex flex-col">
                  
                  {/* Top generated metrics */}
                  {genStats && (
                    <div className="flex items-center justify-between gap-3 bg-darkcard border border-darkborder px-4 py-2.5 rounded-xl mb-4 text-xs font-mono text-gray-300">
                      <div className="flex items-center gap-4 min-w-0 flex-wrap">
                        <span>Latency: <strong className="text-white">{genStats.latency_ms}ms</strong></span>
                        <span>Tokens: <strong className="text-white">{genStats.tokens}</strong></span>
                        <span>Model: <strong className="text-blue-400">{genStats.model}</strong></span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={handleDownloadPdf}
                          disabled={!generatedPrd || loading}
                          className="inline-flex items-center gap-1.5 bg-blue-500/10 text-blue-300 hover:text-white hover:bg-blue-500/20 disabled:opacity-40 px-2 py-1 rounded border border-blue-500/20 transition-colors"
                          title="Download sandbox output as PDF"
                        >
                          <Download className="h-3.5 w-3.5" />
                          PDF
                        </button>
                        <div className="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                          <span>Score:</span>
                          <strong className="font-bold">{genStats.scores?.final_score.toFixed(1)}</strong>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex-1 border border-darkborder bg-[#050811] rounded-xl p-4 overflow-y-auto max-h-[380px] font-mono text-xs text-gray-300 whitespace-pre-wrap">
                    {loading ? (
                      <div className="h-full w-full flex flex-col items-center justify-center text-center gap-3">
                        <RefreshCw className="h-8 w-8 text-brand-500 animate-spin" />
                        <p className="text-gray-400">LangGraph is walking the nodes:<br />
                        <span className="text-[10px] text-gray-500">Loader → Generator → Judge → Postgres DB</span></p>
                      </div>
                    ) : generatedPrd ? (
                      generatedPrd
                    ) : (
                      <div className="h-full w-full flex flex-col items-center justify-center text-center gap-2 text-gray-500">
                        <Cpu className="h-10 w-10 text-gray-600" />
                        <span>Sandbox Output Window</span>
                      </div>
                    )}
                  </div>
                </div>

                {genStats?.scores && (
                  <div className="mt-4 border-t border-darkborder pt-4">
                    <h4 className="text-xs font-semibold text-white mb-3">LLM-as-a-Judge Score Metrics Details</h4>
                    <div className="grid grid-cols-4 gap-2 text-center text-xs">
                      {[
                        { label: "Coverage", score: genStats.scores.coverage, color: "text-emerald-400" },
                        { label: "Factuality", score: genStats.scores.hallucination, color: "text-blue-400" },
                        { label: "Design", score: genStats.scores.design, color: "text-indigo-400" },
                        { label: "Engineering", score: genStats.scores.engineering, color: "text-indigo-400" },
                        { label: "QA Cases", score: genStats.scores.qa, color: "text-purple-400" },
                        { label: "Prototype", score: genStats.scores.prototype, color: "text-purple-400" },
                        { label: "Repetition", score: genStats.scores.repetition, color: "text-rose-400" },
                        { label: "Format", score: genStats.scores.format, color: "text-rose-400" }
                      ].map(metric => (
                        <div key={metric.label} className="bg-darkcard border border-darkborder p-2 rounded-lg">
                          <span className="text-[10px] text-gray-400 block truncate">{metric.label}</span>
                          <strong className={`font-mono text-sm mt-0.5 block ${metric.color}`}>{metric.score.toFixed(0)}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>

            </div>
          )}

          {activeTab === 'registry' && (
            <div className="glass p-6 rounded-2xl flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-darkborder pb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">Registry Prompt Config</h3>
                  <p className="text-xs text-gray-400">Modify prompts loaded dynamically at runtime without restarting services or deploying code.</p>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={editingVersion}
                    onChange={(e) => setEditingVersion(e.target.value)}
                    className="bg-darkcard border border-darkborder rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
                  >
                    <option value="v1">v1.md (Basic)</option>
                    <option value="v2">v2.md (Structured)</option>
                    <option value="v3">v3.md (Principal PM/Optimized)</option>
                  </select>
                  <button
                    onClick={handleSavePrompt}
                    disabled={loading}
                    className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-xl text-sm transition-all shadow-md shadow-brand-500/10"
                  >
                    Save Changes
                  </button>
                </div>
              </div>

              <div className="relative">
                <textarea
                  rows={20}
                  value={promptContent}
                  onChange={(e) => setPromptContent(e.target.value)}
                  className="w-full bg-[#050811] border border-darkborder rounded-xl p-4 font-mono text-xs text-gray-300 focus:outline-none focus:border-brand-500 resize-y"
                  placeholder="Paste prompt markdown template content here..."
                />
                {!backendOnline && (
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-[1px] flex flex-col items-center justify-center text-center p-6 rounded-xl">
                    <AlertCircle className="h-10 w-10 text-rose-500 mb-2" />
                    <h4 className="font-semibold text-white mb-1">Editor Offline</h4>
                    <p className="text-xs text-gray-400 max-w-xs">The Prompt Registry editor is disabled when running in frontend mocked mode. Connect the FastAPI backend to use dynamic prompt configuration.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-darkborder py-6 text-center text-xs text-gray-500 bg-[#0B0F19]">
        <p>© 2026 ProductOS. Built for AI Architect evaluation and prompt optimization.</p>
      </footer>
    </div>
  );
}
