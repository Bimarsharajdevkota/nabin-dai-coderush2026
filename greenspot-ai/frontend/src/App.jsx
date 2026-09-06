import React, { useState } from 'react';
import { Leaf, Server, Zap, BarChart3, CloudRain, ChevronDown, Terminal, ShieldAlert, Cpu, X } from 'lucide-react';
import EarthGlobe from './components/EarthGlobe';
import { motion, AnimatePresence } from 'framer-motion';
import { regionsData } from './regionsData';

function App() {
  const [layerMode, setLayerMode] = useState('carbon');
  const [selectedRegion, setSelectedRegion] = useState(null);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 font-sans selection:bg-emerald-500/30">
      
      {/* 3D Background */}
      <div className="fixed inset-0 z-0">
        <EarthGlobe layerMode={layerMode} onRegionSelect={setSelectedRegion} />
        <div className="absolute inset-0 bg-gradient-to-b from-neutral-950/20 via-transparent to-neutral-950/90 pointer-events-none" />
      </div>

      {/* Floating Interactive Panel */}
      <AnimatePresence>
        {selectedRegion && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, x: 20 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.9, x: 20 }}
            className="fixed bottom-8 right-8 z-50 w-80 bg-neutral-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl"
          >
            <button 
              onClick={() => setSelectedRegion(null)}
              className="absolute top-4 right-4 text-neutral-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
            <h4 className="text-sm font-bold text-white mb-1 uppercase tracking-wider">{selectedRegion.name}</h4>
            <div className="text-xs text-neutral-400 mb-4">{selectedRegion.id}</div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-white/5">
                <span className="text-sm text-neutral-400">Carbon Intensity</span>
                <span className={`text-sm font-bold ${selectedRegion.carbon > 400 ? 'text-red-400' : selectedRegion.carbon > 150 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {selectedRegion.carbon} gCO₂/kWh
                </span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-white/5">
                <span className="text-sm text-neutral-400">Spot Price (g4dn.xl)</span>
                <span className="text-sm font-bold text-white">{selectedRegion.cost}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-white/5">
                <span className="text-sm text-neutral-400">Primary Source</span>
                <span className="text-sm font-bold text-blue-400">{selectedRegion.source}</span>
              </div>
              <div className="flex justify-between items-center pt-1">
                <span className="text-sm text-neutral-400">Pareto Score</span>
                <span className={`text-sm font-bold ${selectedRegion.score > 80 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {selectedRegion.score}/100
                </span>
              </div>
            </div>
            
            <a href="/dashboard" className="mt-5 w-full block text-center bg-emerald-500 hover:bg-emerald-400 text-black py-2 rounded-xl text-sm font-bold transition-colors">
              Deploy Workload Here
            </a>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-40 border-b border-white/5 bg-neutral-950/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Leaf className="w-6 h-6 text-emerald-500" />
            <span className="text-xl font-serif tracking-wide font-medium">GreenSpot AI</span>
          </div>
          <div className="hidden md:flex gap-8 text-sm font-medium text-neutral-400">
            <a href="#problem" className="hover:text-white transition-colors">The Crisis</a>
            <a href="#arbitrage" className="hover:text-white transition-colors">Pareto Engine</a>
            <a href="#resilience" className="hover:text-white transition-colors">IMDSv2 Runtime</a>
            <a href="#receipts" className="hover:text-white transition-colors">ESG Receipts</a>
          </div>
          <a href="/dashboard" className="bg-white text-black px-5 py-2 rounded-full text-sm font-medium hover:bg-neutral-200 transition-colors inline-block text-center shadow-[0_0_15px_rgba(255,255,255,0.2)]">
            Launch Platform
          </a>
        </div>
      </nav>

      {/* SECTION 1: Hero */}
      <section className="relative z-10 pt-40 pb-20 px-6 min-h-screen flex flex-col items-center pointer-events-none">
        <div className="max-w-4xl mx-auto text-center mt-20 pointer-events-auto">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 backdrop-blur-md"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-medium tracking-widest uppercase text-neutral-300">Live Interactive Globe (Click Regions)</span>
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-5xl md:text-7xl font-serif tracking-tight leading-tight mb-8 drop-shadow-2xl"
          >
            Cloud Compute, <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-200">Priced by the Planet.</span>
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-lg md:text-xl text-neutral-300 font-light max-w-2xl mx-auto leading-relaxed mb-12 drop-shadow-xl"
          >
            Find the cheapest, cleanest place on Earth to run your AI models. Our engine automatically arbitrages AWS spot pricing and real-time grid carbon intensity.
          </motion.p>
        </div>

        {/* Floating Globe Controls */}
        <div className="mt-auto mb-10 w-full max-w-md mx-auto bg-neutral-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-2 flex flex-col md:flex-row gap-2 pointer-events-auto shadow-2xl">
          <button 
            onClick={() => setLayerMode('carbon')}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${layerMode === 'carbon' ? 'bg-white/10 text-white shadow-lg' : 'text-neutral-400 hover:text-white hover:bg-white/5'}`}
          >
            <div className={`w-2 h-2 rounded-full ${layerMode === 'carbon' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-neutral-600'}`} />
            Carbon Footprint
          </button>
          <button 
            onClick={() => setLayerMode('sources')}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${layerMode === 'sources' ? 'bg-white/10 text-white shadow-lg' : 'text-neutral-400 hover:text-white hover:bg-white/5'}`}
          >
            <div className={`w-2 h-2 rounded-full ${layerMode === 'sources' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-neutral-600'}`} />
            Clean Energy %
          </button>
        </div>
        <ChevronDown className="w-6 h-6 text-neutral-500 animate-bounce mt-4 pointer-events-auto" />
      </section>

      {/* SECTION 2: The Problem (Carbon Crisis) */}
      <section id="problem" className="py-32 px-6 max-w-4xl mx-auto relative z-10 text-center">
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
        >
          <h3 className="text-sm uppercase tracking-widest text-emerald-500 font-semibold mb-4">01 // The Crisis</h3>
          <h2 className="text-4xl md:text-5xl font-serif mb-8">AI is Burning the Planet</h2>
          <p className="text-xl text-neutral-400 font-light leading-relaxed mb-6">
            Data center emissions have skyrocketed by 300% since the AI boom. Every day, engineering teams spin up massive GPU clusters in default cloud regions like <code className="text-red-400 bg-red-400/10 px-2 py-1 rounded">us-east-1 (N. Virginia)</code>, which relies heavily on fossil fuels (410g CO₂/kWh).
          </p>
          <p className="text-xl text-neutral-400 font-light leading-relaxed">
            They pay full on-demand pricing, completely unaware that a <span className="text-emerald-400 font-medium">70% cheaper, near-zero-carbon spot instance</span> is sitting idle in Montreal or Stockholm, powered by 100% clean hydroelectricity.
          </p>
        </motion.div>
      </section>

      {/* SECTION 3: The Arbitrage Engine (Backend Component 1) */}
      <section id="arbitrage" className="py-32 bg-neutral-900/50 border-y border-white/5 relative z-10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-16 items-center">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h3 className="text-sm uppercase tracking-widest text-emerald-500 font-semibold mb-4">02 // greenspot.core.scorer</h3>
            <h2 className="text-3xl md:text-5xl font-serif mb-6 leading-tight">The Pareto Arbitrage Engine.</h2>
            <p className="text-neutral-400 text-lg mb-8 leading-relaxed">
              To solve this, we built a Python backend that exploits two variables that fluctuate independently every single hour: AWS Spot discounts and regional grid carbon intensity. Our engine evaluates a mathematical Pareto curve to find the absolute optimal region.
            </p>
            <div className="space-y-6 text-neutral-400">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-white/5 rounded-xl text-white">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-white font-medium text-lg">Real-Time Spot APIs</h4>
                  <p className="text-sm leading-relaxed mt-1">Ingesting `boto3` pricing for EC2 g4dn/g5 GPU instances globally. Prices drop by up to 90% during off-peak hours.</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-white/5 rounded-xl text-white">
                  <CloudRain className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-white font-medium text-lg">Live Carbon Telemetry</h4>
                  <p className="text-sm leading-relaxed mt-1">Cross-referencing pricing with Electricity Maps API. When the sun shines in California, solar floods the grid, and carbon footprints drop to zero.</p>
                </div>
              </div>
            </div>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="bg-neutral-950 border border-white/10 rounded-3xl p-8 shadow-2xl"
          >
             <h4 className="text-xl font-serif mb-6 text-white flex items-center justify-between">
               Live Radar Output
               <span className="text-xs font-mono text-emerald-500">GET /api/radar</span>
             </h4>
             <div className="space-y-4">
               {regionsData.slice(0, 4).map((item, i) => (
                 <div key={i} className="flex items-center justify-between p-4 bg-neutral-900 rounded-xl border border-white/5 hover:border-emerald-500/30 transition-colors">
                   <div>
                     <div className="text-sm font-medium text-white">{item.name}</div>
                     <div className="text-xs text-neutral-500 mt-1">{item.carbon} CO₂/kWh • {item.cost}</div>
                   </div>
                   <div className={`px-3 py-1 rounded-full text-xs font-bold ${item.score > 80 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-neutral-800 text-neutral-400'}`}>
                     {item.score} Score
                   </div>
                 </div>
               ))}
             </div>
          </motion.div>
        </div>
      </section>

      {/* SECTION 4: Resilience Runtime (Backend Component 2) */}
      <section id="resilience" className="py-32 px-6 max-w-7xl mx-auto relative z-10">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="order-2 md:order-1 bg-neutral-900 rounded-3xl p-8 border border-white/10 shadow-2xl font-mono text-sm text-neutral-300"
          >
            <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-4">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-amber-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="ml-2 text-neutral-500 text-xs">greenspot/runtime/checkpoint.py</span>
            </div>
            <pre className="overflow-x-auto leading-relaxed">
<span className="text-purple-400">@checkpoint_protect</span>
<span className="text-blue-400">def</span> <span className="text-yellow-200">train_model</span>():
    <span className="text-neutral-500"># Background daemon polls AWS IMDSv2 metadata</span>
    <span className="text-blue-400">while</span> <span className="text-orange-300">True</span>:
        <span className="text-blue-400">if</span> aws_imds_preemption_notice():
            logger.warning(<span className="text-green-300">"SPOT EVICTION DETECTED!"</span>)
            
            <span className="text-neutral-500"># Instantly backup ML weights to blob storage</span>
            s3.flush_weights(model.state)
            
            <span className="text-blue-400">raise</span> SpotEvictionError()
        model.step()
            </pre>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="order-1 md:order-2"
          >
            <h3 className="text-sm uppercase tracking-widest text-emerald-500 font-semibold mb-4">03 // greenspot.runtime</h3>
            <h2 className="text-3xl md:text-5xl font-serif mb-6">AWS IMDSv2 Fault Tolerance.</h2>
            <p className="text-neutral-400 text-lg mb-6 leading-relaxed">
              Running on AWS Spot instances is cheap, but Amazon can kill your server at any moment with exactly 2 minutes of warning. To make this production-ready, we built a highly resilient runtime environment.
            </p>
            <p className="text-neutral-400 text-lg leading-relaxed">
              Our background daemon constantly polls the AWS EC2 metadata endpoints. When a preemption notice is detected, our <code className="text-white bg-white/10 px-2 py-1 rounded">@checkpoint_protect</code> decorator intercepts the signal, halts your PyTorch training loop, instantly flushes your model weights to S3, and cleanly shuts down the server.
            </p>
          </motion.div>
        </div>
      </section>

      {/* SECTION 5: ESG Receipts (Backend Component 3) */}
      <section id="receipts" className="py-32 bg-neutral-900/50 border-y border-white/5 relative z-10 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div 
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <ShieldAlert className="w-12 h-12 text-emerald-400 mx-auto mb-6" />
            <h3 className="text-sm uppercase tracking-widest text-emerald-500 font-semibold mb-4">04 // greenspot.api.history</h3>
            <h2 className="text-4xl md:text-5xl font-serif mb-8">Verifiable ESG Cryptographic Receipts</h2>
            <p className="text-xl text-neutral-400 font-light leading-relaxed mb-12">
              Corporate sustainability reporting shouldn't be guesswork. Every workload successfully routed by the GreenSpot FastAPI server generates an immutable Pydantic schema containing exact carbon footprints and dollar savings, globally queryable via <code className="text-white">GET /api/history</code>.
            </p>
            <div className="bg-neutral-950 p-6 rounded-2xl border border-emerald-500/30 text-left font-mono text-sm text-emerald-400/80 inline-block shadow-2xl">
              {`{
  "job_id": "gs_94f8a21_aws",
  "status": "COMPLETED",
  "region_executed": "eu-north-1",
  "carbon_avoided_g": 3105.4,
  "dollars_saved_usd": 12.40,
  "preemptions_handled": 1,
  "blockchain_hash": "0x4a9b..."
}`}
            </div>
          </motion.div>
        </div>
      </section>

      {/* SECTION 6: Developer CLI (Backend Component 4) */}
      <section className="py-32 px-6 max-w-7xl mx-auto relative z-10">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h3 className="text-sm uppercase tracking-widest text-emerald-500 font-semibold mb-4">05 // greenspot_cli.py</h3>
            <h2 className="text-3xl md:text-5xl font-serif mb-6">Open Source CLI.</h2>
            <p className="text-neutral-400 text-lg mb-6 leading-relaxed">
              We built GreenSpot for developers. Using Typer and Rich, we exposed our entire FastAPI backend directly into your terminal, allowing MLOps engineers to integrate GreenSpot natively into their bash scripts.
            </p>
            <ul className="space-y-4 text-neutral-400">
              <li className="flex items-center gap-3"><Terminal className="w-5 h-5 text-emerald-500"/> <code className="text-white bg-white/5 px-2 py-1 rounded">greenspot radar</code> - View live pareto tables</li>
              <li className="flex items-center gap-3"><Cpu className="w-5 h-5 text-blue-500"/> <code className="text-white bg-white/5 px-2 py-1 rounded">greenspot run --task train.py</code> - Dispatch workload</li>
            </ul>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="bg-black rounded-3xl p-8 border border-white/10 shadow-2xl font-mono text-sm leading-relaxed"
          >
            <div className="text-neutral-500 mb-2">$ greenspot run --task "python ml_train.py"</div>
            <div className="text-blue-400 mb-2">[INFO] Arbitrage Engine analyzing 24 global regions...</div>
            <div className="text-emerald-400 mb-4">[SUCCESS] Selected eu-north-1 (Stockholm).</div>
            <div className="text-neutral-300">Executing workload inside Docker container...</div>
            <div className="text-neutral-500 mt-4">... 1.2 hrs later ...</div>
            <div className="text-emerald-400 font-bold mt-4">Job Completed Successfully.</div>
            <div className="text-white">Receipt ID: gs_98b73a</div>
            <div className="text-white">Carbon Avoided: 840g CO2</div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-neutral-950 py-12 relative z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-sm text-neutral-500">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <Leaf className="w-5 h-5 text-emerald-600" />
            <span>© 2026 GreenSpot AI Platform. A Hackathon Project.</span>
          </div>
          <div className="flex gap-6">
            <a href="https://github.com" className="hover:text-white transition-colors">GitHub Repo</a>
            <a href="/dashboard" className="text-emerald-500 hover:text-emerald-400 font-medium transition-colors">Launch Dashboard</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
