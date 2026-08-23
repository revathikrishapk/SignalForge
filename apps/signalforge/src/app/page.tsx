"use client";

import React, { useState } from "react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import {
  Search,
  Sparkles,
  BrainCircuit,
  Zap,
  Target,
  Loader2,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  ExternalLink,
} from "lucide-react";

// --- Types matching your FastAPI ResearchResponse + sources ---
interface ResearchInsight {
  title: string;
  summary: string;
  impact_score: number;
}

interface ResearchSource {
  title: string;
  snippet: string;
  url: string;
  date: string;
}

interface SignalForgeData {
  executive_summary: string;
  key_insights: ResearchInsight[];
  market_signals: string[];
  recommended_actions: string[];
  sources?: ResearchSource[];
}

// --- Animation Variants ---
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { type: "spring", stiffness: 100 },
  },
};

export default function SignalForgeModernUI() {
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
    setData(null);

    try {
      const response = await fetch(
        "https://signalforge-1szp.onrender.com/api/research/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic, depth }),
        }
      );

      if (!response.ok)
        throw new Error(`Analysis failed (Status: ${response.status})`);
      const result: SignalForgeData = await response.json();
      setData(result);
    } catch (err: any) {
      setError(
        err.message || "An unexpected error occurred during research synthesis."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans">
      {/* Header */}
      <nav className="bg-white/95 backdrop-blur-sm sticky top-0 z-50 border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-sky-600 rounded-xl shadow-md shadow-sky-100">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tighter text-slate-950">
              SignalForge<span className="text-sky-600">.</span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">
              Powered by Gemini 2.5 Flash
            </span>
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-12 md:py-16">
        {/* Search Header */}
        <section className="text-center max-w-3xl mx-auto mb-16 md:mb-20">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-50 text-sky-700 border border-sky-100 text-sm font-medium mb-5">
              <Zap className="w-4 h-4" />
              Next-Gen Market Intelligence
            </span>
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tighter text-slate-950 leading-[1.1] mb-6">
              Synthesize complex topics into{" "}
              <span className="text-sky-600">actionable insights.</span>
            </h2>
            <p className="text-lg text-slate-600 mb-10 leading-relaxed">
              Enter any technology, academic paper subject, or market trend to synthesize real-time arXiv literature and ground insights.
            </p>
          </motion.div>

          {/* Form */}
          <motion.form
            onSubmit={handleSearch}
            className="p-2 bg-white rounded-full shadow-lg border border-slate-100 flex items-center gap-2 hover:shadow-xl hover:border-slate-200 transition-all duration-300"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <Search className="w-6 h-6 text-slate-400 ml-4 flex-shrink-0" />
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Retrieval Augmented Generation, Quantum Machine Learning..."
              className="flex-1 py-3 px-2 text-base text-slate-900 placeholder-slate-400 bg-transparent focus:outline-none"
              required
            />
            <div className="h-8 w-px bg-slate-100" />
            <select
              value={depth}
              onChange={(e) => setDepth(e.target.value)}
              className="py-3 px-4 text-sm text-slate-600 bg-transparent focus:outline-none cursor-pointer"
            >
              <option value="standard">Standard</option>
              <option value="overview">Overview</option>
              <option value="deep">Deep Dive</option>
            </select>
            <button
              type="submit"
              disabled={loading}
              className="px-7 py-3 bg-slate-950 hover:bg-slate-800 disabled:bg-slate-400 text-white font-semibold rounded-full text-sm flex items-center gap-2 transition cursor-pointer flex-shrink-0"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Analyze"
              )}
              <ArrowRight className="w-4 h-4" />
            </button>
          </motion.form>
        </section>

        {/* Results */}
        <AnimatePresence mode="wait">
          {loading && (
            <motion.div
              key="loading"
              initial="hidden"
              animate="visible"
              exit="hidden"
              variants={containerVariants}
              className="text-center py-20 bg-slate-50 rounded-3xl border border-slate-100"
            >
              <Loader2 className="w-12 h-12 animate-spin text-sky-600 mx-auto mb-6" />
              <h3 className="text-xl font-semibold text-slate-900">
                Synthesizing Intelligence...
              </h3>
              <p className="text-slate-600 mt-2">
                Fetching arXiv literature & running Gemini 2.5 Flash for &apos;{topic}&apos;
              </p>
            </motion.div>
          )}

          {error && (
            <motion.div
              key="error"
              initial="hidden"
              animate="visible"
              exit="hidden"
              variants={containerVariants}
              className="p-6 bg-amber-50 border border-amber-200 rounded-2xl text-amber-900 flex items-center gap-4 max-w-2xl mx-auto"
            >
              <AlertTriangle className="w-10 h-10 text-amber-500 flex-shrink-0" />
              <div>
                <h4 className="font-bold">Analysis Interrupted</h4>
                <p className="text-sm text-amber-800">{error}</p>
              </div>
            </motion.div>
          )}

          {data && !loading && (
            <motion.div
              key="results"
              initial="hidden"
              animate="visible"
              variants={containerVariants}
              className="space-y-10"
            >
              {/* Executive Summary */}
              <motion.div
                variants={itemVariants}
                className="p-8 bg-slate-50 rounded-3xl border border-slate-100 shadow-inner"
              >
                <div className="flex items-center gap-3 mb-5">
                  <BrainCircuit className="w-7 h-7 text-sky-600" />
                  <h3 className="text-2xl font-bold tracking-tight text-slate-950">
                    Synthesis Summary
                  </h3>
                </div>
                <p className="text-lg text-slate-800 leading-relaxed font-medium bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
                  {data.executive_summary}
                </p>
              </motion.div>

              {/* Main Content Grid */}
              <div className="grid grid-cols-1 md:grid-cols-[2fr,1fr] gap-10">
                {/* Key Insights */}
                <div className="space-y-6">
                  <motion.h4
                    variants={itemVariants}
                    className="text-sm font-semibold text-slate-500 uppercase tracking-wider"
                  >
                    Core Technical &amp; Market Insights
                  </motion.h4>
                  {data.key_insights.map((insight, idx) => (
                    <motion.div
                      key={idx}
                      variants={itemVariants}
                      className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow duration-300"
                    >
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <h5 className="text-lg font-semibold text-slate-950 leading-snug">
                          {insight.title}
                        </h5>
                        <div className="text-center flex-shrink-0">
                          <div className="text-xs text-slate-500 font-medium">
                            IMPACT
                          </div>
                          <div
                            className={`text-2xl font-extrabold ${
                              insight.impact_score >= 8
                                ? "text-emerald-600"
                                : insight.impact_score >= 5
                                ? "text-sky-600"
                                : "text-slate-500"
                            }`}
                          >
                            {insight.impact_score}
                            <span className="text-sm text-slate-400">/10</span>
                          </div>
                        </div>
                      </div>
                      <p className="text-base text-slate-700 leading-relaxed">
                        {insight.summary}
                      </p>
                    </motion.div>
                  ))}
                </div>

                {/* Sidebar */}
                <div className="space-y-10">
                  {/* Market Signals */}
                  <motion.div
                    variants={itemVariants}
                    className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm"
                  >
                    <h4 className="text-lg font-bold text-slate-950 mb-5 flex items-center gap-2.5">
                      <Zap className="w-5 h-5 text-amber-500" />
                      Emerging Signals
                    </h4>
                    <ul className="space-y-3.5">
                      {data.market_signals.map((signal, idx) => (
                        <li
                          key={idx}
                          className="flex items-start gap-3 text-slate-700 text-sm leading-relaxed"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2 flex-shrink-0" />
                          {signal}
                        </li>
                      ))}
                    </ul>
                  </motion.div>

                  {/* Actions */}
                  <motion.div
                    variants={itemVariants}
                    className="p-6 bg-white rounded-2xl border border-slate-100 shadow-sm"
                  >
                    <h4 className="text-lg font-bold text-slate-950 mb-5 flex items-center gap-2.5">
                      <Target className="w-5 h-5 text-emerald-600" />
                      Recommended Actions
                    </h4>
                    <ul className="space-y-3.5">
                      {data.recommended_actions.map((action, idx) => (
                        <li
                          key={idx}
                          className="flex items-start gap-3 text-slate-700 text-sm leading-relaxed"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 flex-shrink-0" />
                          {action}
                        </li>
                      ))}
                    </ul>
                  </motion.div>

                  {/* Retrieved Sources Section */}
                  {data.sources && data.sources.length > 0 && (
                    <motion.div
                      variants={itemVariants}
                      className="p-6 bg-slate-50 rounded-2xl border border-slate-100 shadow-sm"
                    >
                      <h4 className="text-lg font-bold text-slate-950 mb-4 flex items-center gap-2.5">
                        <BookOpen className="w-5 h-5 text-sky-600" />
                        Grounded Sources ({data.sources.length})
                      </h4>
                      <div className="space-y-3">
                        {data.sources.map((source, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-white rounded-xl border border-slate-100 text-xs"
                          >
                            <span className="font-bold text-sky-700">
                              [{idx + 1}]
                            </span>{" "}
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noreferrer"
                              className="font-medium text-slate-900 hover:underline inline-flex items-center gap-1 ml-1"
                            >
                              {source.title}
                              <ExternalLink className="w-3 h-3 text-slate-400" />
                            </a>
                            <p className="text-slate-500 mt-1 line-clamp-2">
                              {source.snippet}
                            </p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="border-t border-slate-100 mt-24">
        <div className="max-w-7xl mx-auto px-6 py-8 text-center text-sm text-slate-500">
          &copy; 2026 AI Engineering Lab. All rights reserved. SignalForge Pro
          v1.0
        </div>
      </footer>
    </div>
  );
}