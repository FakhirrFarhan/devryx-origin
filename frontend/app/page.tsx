"use client";

import { useMemo, useState } from "react";
import {
  Aperture, ArrowDownToLine, AudioLines, Bell, ChevronDown, ChevronLeft,
  ChevronRight, CircleHelp, Clapperboard, Clock3, CloudUpload, Command,
  Film, FolderOpen, Image as ImageIcon, Layers3, Library, Maximize2,
  MoreHorizontal, Play, Plus, Settings2, SlidersHorizontal, Sparkles,
  Square, WandSparkles, X, Zap
} from "lucide-react";

type Job = { id: string; prompt: string; type: string; status: string; created_at: string };

const recentItems = [
  { name: "Neon Horizon", meta: "Video · 8 seconds", tone: "from-indigo-950 via-blue-900 to-orange-800" },
  { name: "Quiet Geometry", meta: "Image · 16:9", tone: "from-stone-700 via-zinc-500 to-amber-200" },
  { name: "After the Rain", meta: "Video · 5 seconds", tone: "from-slate-900 via-cyan-950 to-emerald-700" },
];

export default function Home() {
  const [mode, setMode] = useState<"video" | "image">("video");
  const [prompt, setPrompt] = useState("A cinematic tracking shot through a quiet futuristic city after rainfall, reflections across dark glass, soft atmospheric haze, restrained amber highlights.");
  const [model, setModel] = useState("Video model · not connected");
  const [ratio, setRatio] = useState("16:9");
  const [duration, setDuration] = useState("5 seconds");
  const [quality, setQuality] = useState("720p preview");
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("Create");
  const [showSettings, setShowSettings] = useState(true);
  const [playing, setPlaying] = useState(false);

  const durationLabel = useMemo(() => duration.replace(" seconds", "s"), [duration]);

  async function createJob() {
    if (prompt.trim().length < 3) {
      setError("Add a prompt with at least 3 characters.");
      return;
    }
    setLoading(true); setError(""); setJob(null);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/generations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, generation_type: mode }),
      });
      if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}`);
      const data = await response.json();
      setJob(data.job);
    } catch (e) {
      setError(e instanceof Error ? `${e.message}. Start the local backend on port 8000.` : "Could not contact backend.");
    } finally { setLoading(false); }
  }

  return (
    <main className="min-h-screen bg-[#090a0c] text-[#f2f2f0]">
      <div className="flex min-h-screen">
        <aside className="hidden w-[76px] shrink-0 flex-col items-center border-r border-white/[0.07] bg-[#0c0d10] py-5 lg:flex">
          <div className="mb-10 flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-[#d7b9f7] to-[#a879d4] text-[#21172b]">
            <Aperture size={22} strokeWidth={2.4}/>
          </div>
          <div className="flex flex-1 flex-col items-center gap-3">
            {[
              { icon: Clapperboard, label: "Create" },
              { icon: Library, label: "Library" },
              { icon: Layers3, label: "Models" },
              { icon: FolderOpen, label: "Projects" },
            ].map(({icon: Icon, label}) => (
              <button key={label} title={label} onClick={() => setActiveTab(label)}
                className={`flex h-11 w-11 items-center justify-center rounded-xl transition ${activeTab === label ? "bg-white/10 text-[#d5b7f5]" : "text-[#777b83] hover:bg-white/[0.06] hover:text-white"}`}>
                <Icon size={19}/>
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-3">
            <button title="Help" className="flex h-10 w-10 items-center justify-center rounded-xl text-[#777b83] hover:bg-white/[0.06]"><CircleHelp size={18}/></button>
            <button title="Settings" className="flex h-10 w-10 items-center justify-center rounded-xl text-[#777b83] hover:bg-white/[0.06]"><Settings2 size={18}/></button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-[#22252b] text-xs font-semibold">FF</div>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-white/[0.07] bg-[#111219]/45 px-5 backdrop-blur-2xl md:px-8">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#d7b9f7] to-[#a879d4] text-[#21172b] lg:hidden"><Aperture size={18}/></div>
              <div>
                <div className="text-[13px] font-semibold tracking-[.16em]">AI STUDIO <span className="text-[#d5b7f5]">/</span> WORKSPACE</div>
                <div className="mt-1 text-[11px] text-[#777b83]">Untitled project <span className="px-1.5 text-[#45484e]">·</span> Saved locally</div>
              </div>
            </div>
            <div className="flex items-center gap-2 md:gap-4">
              <div className="hidden items-center gap-2 rounded-full border border-white/[0.08] px-3 py-1.5 text-[11px] text-[#969aa2] sm:flex"><span className="h-1.5 w-1.5 rounded-full bg-[#c9a6f5]"/> Local workspace</div>
              <button className="hidden rounded-lg border border-white/10 px-3 py-2 text-xs text-[#b6b8bd] hover:bg-white/5 sm:block">Share</button>
              <button className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#c6a0ed] to-[#d69acb] px-3.5 py-2.5 text-xs font-semibold text-[#21172b] hover:brightness-110"><CloudUpload size={14}/> Export</button>
              <button className="rounded-lg p-2 text-[#858992] hover:bg-white/5"><Bell size={17}/></button>
            </div>
          </header>

          <div className="studio-scroll flex-1 overflow-auto">
            <div className="mx-auto max-w-[1600px] p-4 md:p-7">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-1 rounded-xl border border-white/[0.08] bg-[#111317] p-1">
                  <button onClick={() => setMode("video")} className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-xs font-medium transition ${mode === "video" ? "bg-[#292d32] text-white shadow" : "text-[#777b83] hover:text-white"}`}><Film size={15}/> Video</button>
                  <button onClick={() => setMode("image")} className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-xs font-medium transition ${mode === "image" ? "bg-[#292d32] text-white shadow" : "text-[#777b83] hover:text-white"}`}><ImageIcon size={15}/> Image</button>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-[#777b83]"><Command size={13}/> <span>Creative workspace</span><span className="text-[#3b3e44]">/</span><span className="text-[#b9bbc0]">{activeTab}</span></div>
              </div>

              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
                <div className="min-w-0 space-y-5">
                  <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#171821]/65 glass-surface">
                    <div className="flex h-12 items-center justify-between border-b border-white/[0.07] px-4">
                      <div className="flex items-center gap-2 text-xs font-medium text-[#d8d9dc]"><span className="h-1.5 w-1.5 rounded-full bg-[#c9a6f5]"/> Preview canvas</div>
                      <div className="flex items-center gap-3 text-[#777b83]">
                        <span className="text-[10px]">{ratio} <span className="text-[#4c5057]">·</span> {quality}</span>
                        <button title="Expand preview" className="hover:text-white"><Maximize2 size={15}/></button>
                        <button title="More options" className="hover:text-white"><MoreHorizontal size={17}/></button>
                      </div>
                    </div>
                    <div className="film-grid relative flex aspect-video items-center justify-center overflow-hidden bg-[#080a0d]">
                      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_45%,rgba(83,105,112,.18),transparent_55%)]"/>
                      <div className="relative mx-auto flex h-full w-full max-w-[900px] items-center justify-center p-4">
                        <div className="relative aspect-video w-full overflow-hidden rounded-md border border-white/[0.08] bg-gradient-to-br from-[#101923] via-[#1a2832] to-[#59402d] shadow-[0_30px_100px_rgba(0,0,0,.45)]">
                          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_72%_36%,rgba(236,164,94,.38),transparent_23%),linear-gradient(180deg,transparent_25%,rgba(5,8,12,.8)_100%)]"/>
                          <div className="absolute bottom-[13%] left-0 right-0 h-[34%] bg-gradient-to-t from-[#080d12] via-[#111b22]/80 to-transparent"/>
                          <div className="absolute bottom-[13%] left-[9%] h-[40%] w-[13%] border-t border-white/10 bg-gradient-to-b from-[#24313a] to-[#0b1016] shadow-xl"/>
                          <div className="absolute bottom-[13%] left-[25%] h-[57%] w-[10%] border-t border-white/10 bg-gradient-to-b from-[#2c3438] to-[#0a1016]"/>
                          <div className="absolute bottom-[13%] right-[13%] h-[48%] w-[16%] border-t border-white/10 bg-gradient-to-b from-[#28343a] to-[#0a1016]"/>
                          <div className="absolute bottom-[13%] right-[32%] h-[32%] w-[9%] bg-gradient-to-b from-[#26343b] to-[#0b1117]"/>
                          <div className="absolute bottom-[13%] left-0 right-0 h-px bg-[#d89a64]/30"/>
                          <div className="absolute bottom-[9%] left-[8%] right-[8%] h-[3%] rounded-full bg-[#d28e5b]/10 blur-xl"/>
                          <div className="absolute left-5 top-5 flex items-center gap-2 rounded-md border border-white/10 bg-black/25 px-2.5 py-1.5 text-[9px] tracking-[.18em] text-white/65 backdrop-blur">SCENE 01 <span className="text-[#d5b7f5]">•</span> PREVIEW</div>
                          <button onClick={() => setPlaying(!playing)} className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/25 bg-black/35 text-white backdrop-blur transition hover:scale-105 hover:bg-black/55">
                            {playing ? <Square size={15} fill="currentColor"/> : <Play size={17} fill="currentColor" className="ml-0.5"/>}
                          </button>
                          <div className="absolute bottom-4 right-4 rounded bg-black/40 px-2 py-1 text-[9px] tracking-wider text-white/60">PREVIEW ONLY</div>
                        </div>
                      </div>
                      <div className="absolute bottom-3 left-4 text-[10px] text-white/35">Canvas preview · generated media will appear here</div>
                    </div>
                    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.07] px-4 py-3">
                      <div className="flex items-center gap-4 text-[10px] text-[#747982]"><span>00:00 / {durationLabel}</span><span>24 FPS target</span><span>{ratio}</span></div>
                      <div className="flex items-center gap-2">
                        <button className="rounded-lg glass-button p-2 text-[#c5b6d5] hover:bg-white/5"><ArrowDownToLine size={14}/></button>
                        <button className="rounded-lg glass-button p-2 text-[#c5b6d5] hover:bg-white/5"><Maximize2 size={14}/></button>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/[0.08] bg-[#171821]/65 glass-surface">
                    <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-3">
                      <div className="flex items-center gap-2 text-xs font-medium"><Clapperboard size={15} className="text-[#d5b7f5]"/> Timeline</div>
                      <div className="flex items-center gap-2 text-[10px] text-[#747982]"><button className="hover:text-white">−</button><span>Fit</span><button className="hover:text-white">+</button><button className="ml-2 hover:text-white"><MoreHorizontal size={16}/></button></div>
                    </div>
                    <div className="studio-scroll overflow-x-auto p-4">
                      <div className="min-w-[560px]">
                        <div className="mb-3 flex justify-between pl-[94px] pr-2 text-[9px] text-[#656a72]"><span>00:00</span><span>00:01</span><span>00:02</span><span>00:03</span><span>00:04</span><span>00:05</span></div>
                        <div className="mb-2 flex gap-2">
                          <div className="flex w-[82px] shrink-0 items-center gap-2 text-[10px] text-[#92969e]"><Film size={13}/> Video 1</div>
                          <div className="relative flex h-12 flex-1 overflow-hidden rounded-md border border-[#9bbd55]/40 bg-[#283323]">
                            <div className="absolute inset-0 flex">
                              {[0,1,2,3,4,5].map((n) => <div key={n} className={`flex-1 border-r border-black/30 ${n%2===0 ? "bg-gradient-to-br from-[#41504a] to-[#182321]" : "bg-gradient-to-br from-[#76543d] to-[#263b3b]"}`}/>)}
                            </div>
                            <div className="relative flex items-center px-3 text-[10px] font-medium text-white/80">Scene 01 · AI generated clip</div>
                          </div>
                        </div>
                        <div className="mb-2 flex gap-2">
                          <div className="flex w-[82px] shrink-0 items-center gap-2 text-[10px] text-[#92969e]"><AudioLines size={13}/> Audio</div>
                          <div className="flex h-8 flex-1 items-center overflow-hidden rounded-md border border-[#477c82]/30 bg-[#15272a] px-3">
                            <div className="flex h-full w-full items-center gap-[3px] opacity-50">{Array.from({length:75},(_,i)=><span key={i} className="w-1 rounded-full bg-[#70b6ad]" style={{height:`${20+((i*17)%70)}%`}}/>)}</div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <div className="flex w-[82px] shrink-0 items-center gap-2 text-[10px] text-[#92969e]"><Plus size={13}/> Add track</div>
                          <button className="h-8 flex-1 rounded-md border border-dashed border-white/10 text-[10px] text-[#666b73] hover:border-white/20 hover:text-white">+ Add media or layer</button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-white/[0.08] bg-[#171821]/65 glass-surface p-4 md:p-5">
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-medium"><Sparkles size={15} className="text-[#d5b7f5]"/> Describe your {mode}</div>
                      <span className="text-[10px] text-[#686d75]">{prompt.length}/2000</span>
                    </div>
                    <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} maxLength={2000} rows={4}
                      placeholder="Describe the scene, subject, movement, lighting and camera direction..."
                      className="w-full resize-y rounded-xl border border-white/[0.07] bg-[#0b0d10]/50 glass-soft p-4 text-[13px] leading-6 text-[#d8d9dc] outline-none placeholder:text-[#555a62] focus:border-[#b98be8]/50"/>
                    <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-[10px] text-[#777b83]"><button className="flex items-center gap-1.5 rounded-lg glass-button px-2.5 py-2 hover:bg-white/5"><Plus size={12}/> Reference</button><button className="flex items-center gap-1.5 rounded-lg glass-button px-2.5 py-2 hover:bg-white/5"><WandSparkles size={12}/> Enhance prompt</button></div>
                      <button onClick={createJob} disabled={loading} className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#c6a0ed] to-[#d69acb] px-5 py-3 text-xs font-bold text-[#21172b] transition hover:brightness-110 disabled:opacity-50"><Sparkles size={14}/>{loading ? "Submitting..." : "Generate"} <span className="ml-1 rounded bg-black/10 px-1.5 py-0.5 text-[9px]">↵</span></button>
                    </div>
                    {error && <p role="alert" className="mt-3 text-xs text-red-400">{error}</p>}
                    {job && <div className="mt-4 rounded-xl border border-[#b98be8]/25 bg-[#b98be8]/[0.06] p-4"><div className="text-xs font-semibold text-[#d5b7f5]">Demo job submitted</div><div className="mt-2 break-all text-[10px] text-[#a8adb5]">Job ID: {job.id}</div><div className="mt-1 text-[10px] text-[#a8adb5]">Status: {job.status} · {job.type}</div><p className="mt-2 text-[10px] text-amber-300/80">No media is generated yet. The inference engine is not connected.</p></div>}
                  </div>
                </div>

                <aside className="space-y-5">
                  <div className="rounded-2xl border border-white/[0.08] bg-[#171821]/65 glass-surface">
                    <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-4">
                      <div className="flex items-center gap-2 text-xs font-semibold"><SlidersHorizontal size={15} className="text-[#d5b7f5]"/> Generation settings</div>
                      <button onClick={() => setShowSettings(!showSettings)} className="text-[#737780] hover:text-white">{showSettings ? <ChevronDown size={16}/> : <ChevronRight size={16}/>}</button>
                    </div>
                    {showSettings && <div className="space-y-5 p-4">
                      <div>
                        <label className="mb-2 block text-[10px] uppercase tracking-[.13em] text-[#777c84]">Model</label>
                        <button onClick={() => setModel(model === "Video model · not connected" ? "Alternative model · not connected" : "Video model · not connected")} className="flex w-full items-center justify-between rounded-lg border border-white/[0.09] bg-[#0b0d10]/55 backdrop-blur-xl px-3 py-3 text-left text-[11px] text-[#d3d5d9]"><span>{model}</span><ChevronDown size={14} className="text-[#777b83]"/></button>
                        <p className="mt-2 text-[10px] leading-4 text-[#666b73]">Model selection becomes active after a local inference engine is installed.</p>
                      </div>
                      <div>
                        <label className="mb-2 block text-[10px] uppercase tracking-[.13em] text-[#777c84]">Aspect ratio</label>
                        <div className="grid grid-cols-3 gap-2">{["16:9","9:16","1:1"].map(v=><button key={v} onClick={()=>setRatio(v)} className={`rounded-lg border py-2.5 text-[11px] ${ratio===v?"border-[#b88ae8]/60 bg-[#b88ae8]/10 text-[#e3c9ff]":"border-white/[0.08] text-[#858a92] hover:bg-white/5"}`}>{v}</button>)}</div>
                      </div>
                      <div>
                        <label className="mb-2 block text-[10px] uppercase tracking-[.13em] text-[#777c84]">Duration</label>
                        <div className="grid grid-cols-3 gap-2">{["5 seconds","8 seconds","10 seconds"].map(v=><button key={v} onClick={()=>setDuration(v)} className={`rounded-lg border py-2.5 text-[10px] ${duration===v?"border-[#b88ae8]/60 bg-[#b88ae8]/10 text-[#e3c9ff]":"border-white/[0.08] text-[#858a92] hover:bg-white/5"}`}>{v.replace(" seconds","s")}</button>)}</div>
                      </div>
                      <div>
                        <label className="mb-2 block text-[10px] uppercase tracking-[.13em] text-[#777c84]">Output quality</label>
                        <button onClick={()=>setQuality(quality==="720p preview"?"1080p target":"720p preview")} className="flex w-full items-center justify-between rounded-lg border border-white/[0.09] bg-[#0b0d10]/55 backdrop-blur-xl px-3 py-3 text-[11px] text-[#d3d5d9]">{quality}<ChevronDown size={14} className="text-[#777b83]"/></button>
                      </div>
                      <div className="rounded-xl border border-white/[0.07] bg-[#0b0d10]/50 glass-soft p-3">
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-medium text-[#c8cbd0]"><Zap size={13} className="text-[#d5b7f5]"/> Local compute</div>
                        <div className="text-[10px] leading-4 text-[#777b83]">GPU availability and model compatibility will be detected during hardware setup.</div>
                      </div>
                    </div>}
                  </div>

                  <div className="rounded-2xl border border-white/[0.08] bg-[#171821]/65 glass-surface p-4">
                    <div className="mb-4 flex items-center justify-between"><span className="text-xs font-semibold">Recent creations</span><button className="text-[10px] text-[#d0a8ee] hover:text-[#e3c9ff]">View all</button></div>
                    <div className="space-y-3">{recentItems.map((item,i)=><button key={item.name} className="flex w-full items-center gap-3 text-left">
                      <div className={`h-[54px] w-[78px] shrink-0 overflow-hidden rounded-lg border border-white/10 bg-gradient-to-br ${item.tone}`}><div className="h-full w-full bg-[linear-gradient(140deg,transparent_35%,rgba(255,255,255,.13)_36%,transparent_60%)]"/></div>
                      <div className="min-w-0 flex-1"><div className="truncate text-[11px] font-medium text-[#d0d2d6]">{item.name}</div><div className="mt-1 text-[10px] text-[#747982]">{item.meta}</div></div><MoreHorizontal size={15} className="text-[#676c74]"/>
                    </button>)}</div>
                  </div>

                  <div className="rounded-2xl border border-[#b88ae8]/15 bg-gradient-to-br from-[#1b2116] to-[#17151f] p-4">
                    <div className="flex items-center gap-2 text-xs font-semibold text-[#e3c8f6]"><Sparkles size={14}/> Studio status</div>
                    <p className="mt-2 text-[10px] leading-5 text-[#b2a1bb]">Interface ready. Local AI models, persistent jobs and media export will be connected in upcoming milestones.</p>
                    <div className="mt-3 flex items-center gap-2 text-[10px] text-[#d2b5e8]"><span className="h-1.5 w-1.5 rounded-full bg-[#c9a6f5]"/> Frontend workspace active</div>
                  </div>
                </aside>
              </div>

              <footer className="mt-8 flex flex-wrap items-center justify-between gap-2 border-t border-white/[0.07] pt-5 text-[10px] text-[#565b63]">
                <span>AI STUDIO · LOCAL DEVELOPMENT BUILD</span>
                <span>Self-hosted infrastructure · No external AI API</span>
              </footer>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
