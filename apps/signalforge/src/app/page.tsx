"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sparkles, TrendingUp, AlertCircle, ShieldCheck, Loader2 } from "lucide-react";

interface ResearchInsight {
  title: str;
  summary: string;
  impact_score: number;
}

interface SignalForgeData {
  topic: string;
  executive_summary: string;
  key_insights: ResearchInsight[];
  market_signals: string[];
  recommended_actions: string[];
}

export default function SignalForgeDashboard() {
  const [topic, setTopic] = useState("");
  const [depth, setDepth] = useState("standard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SignalForgeData | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/research/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, depth }),
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const result: SignalForgeData = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to generate intelligence synthesis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600 rounded-xl shadow-lg shadow-indigo-500/30">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">SignalForge</h1>
              <p className="text-xs text-slate-400">Autonomous Market & Tech Intelligence</p>
            </div>
          </div>
          <span className="text-xs font-medium px-3 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Gemini 2.5 Active
          </span>
        </header>

        {/* Input Form */}
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-500" />
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter research topic (e.g., Quantum Computing in Cryptography)"
              className="w-full pl-12 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 text-slate-100 placeholder-slate-500 transition"
              required
            />
          </div>
          <select
            value={depth}
            onChange={(e) => setDepth(e.target.value)}
            className="px-4 py-3 bg-slate-900 border border-slate-800 rounded-xl focus:outline-none focus:border-indigo-500 text-slate-300"
          >
            <option value="overview">Overview</option>
            <option value="standard">Standard Analysis</option>
            <option value="deep">Deep Tech Investigation</option>
          </select>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900 text-white font-medium rounded-xl flex items-center justify-center gap-2 transition cursor-pointer"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Synthesize"}
          </button>
        </form>

        {/* Error Alert */}
        {error && (
          <div className="p-4 bg-rose-950/50 border border-rose-800/80 rounded-xl text-rose-300 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Dynamic Content Display */}
        <AnimatePresence mode="wait">
          {data && (
            <motion.div
              key={data.topic}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              {/* Executive Summary */}
              <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl">
                <h2 className="text-lg font-semibold text-slate-200 mb-2">Executive Summary</h2>
                <p className="text-slate-300 text-sm leading-relaxed">{data.executive_summary}</p>
              </div>

              {/* Grid Layout for Insights & Signals */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Insights Column */}
                <div className="md:col-span-2 space-y-4">
                  <h3 className="text-md font-semibold text-slate-300 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-indigo-400" />
                    Key Technical Insights
                  </h3>
                  {data.key_insights.map((insight, idx) => (
                    <div key={idx} className="p-5 bg-slate-900/40 border border-slate-800/80 rounded-xl space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-slate-200 text-sm">{insight.title}</h4>
                        <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                          Impact: {insight.impact_score}/10
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 leading-normal">{insight.summary}</p>
                    </div>
                  ))}
                </div>

                {/* Signals & Recommendations */}
                <div className="space-y-6">
                  {/* Signals */}
                  <div className="p-5 bg-slate-900/40 border border-slate-800/80 rounded-xl space-y-3">
                    <h3 className="text-sm font-semibold text-slate-300">Market Signals</h3>
                    <ul className="space-y-2">
                      {data.market_signals.map((signal, idx) => (
                        <li key={idx} className="text-xs text-slate-400 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0"></span>
                          {signal}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Recommended Actions */}
                  <div className="p-5 bg-slate-900/40 border border-slate-800/80 rounded-xl space-y-3">
                    <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      Recommended Actions
                    </h3>
                    <ul className="space-y-2">
                      {data.recommended_actions.map((action, idx) => (
                        <li key={idx} className="text-xs text-slate-400 flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0"></span>
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}