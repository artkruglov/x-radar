import type { CSSProperties } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { CAPTIONS, DURATION, LINES, scene } from "./cues";
import { TH, BRAND } from "./theme";

// Fictional content. Replace these eight scene cards for a real episode.
const CARDS = [
  ["ХУК", "Агент ждёт вашего решения", "Четыре вымышленные истории для проверки шаблона"],
  ["МОДЕЛИ", "Черновик можно проверить", "Вымышленная лаборатория · источник в примере"],
  ["КОДИНГ", "Ревью до отправки", "Вымышленный агент · контрольная точка"],
  ["ДОЛГИЕ ЗАДАЧИ", "Продолжить после сбоя", "Вымышленный движок · сохранение состояния"],
  ["РАБОТА", "Из заметок — в черновик", "Вымышленный помощник · внешнее действие отдельно"],
  ["МОЛНИЯ", "Контекст · ревью · цена · доклад", "Каждый пункт — факт, источник и последствие"],
  ["ЗАМЕТКИ", "Где нужно решение человека?", "Выберите один процесс и проверьте границы действий"],
  ["ДАЛЬШЕ", "Память и качество", "Какую задачу вы доверили бы агенту после проверки?"],
];

export function Film({ vertical }: { fps: number; vertical: boolean }) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const active = CARDS.findIndex((_, i) => { const [a, b] = scene(`s${i + 1}`); return t >= a && t < b; });
  const index = active < 0 ? CARDS.length - 1 : active;
  const [label, headline, detail] = CARDS[index];
  const [start] = scene(`s${index + 1}`);
  const progress = Math.max(0, Math.min(1, (t - start) / 0.4));
  const caption = CAPTIONS.find(c => t >= c.start && t < c.end);
  const font: CSSProperties = { fontFamily: "Arial, sans-serif" };
  const card = <div style={{ width: 1080, height: 1920, position: "relative", overflow: "hidden", background: TH.ink, color: "white", ...font }}>
    <div style={{ position: "absolute", width: 1200, height: 1200, top: 600, left: 200, borderRadius: "50%", background: `radial-gradient(circle, ${TH.accent}40, transparent 68%)`, transform: `scale(${1 + t * 0.001})` }} />
    <div style={{ position: "absolute", left: 48, top: 40, width: 984, height: 8, background: "#ffffff30" }}><div style={{ height: 8, width: `${100 * t / DURATION}%`, background: TH.accent }} /></div>
    <div style={{ position: "absolute", top: 90, left: 56, fontSize: 32 }}>{BRAND.channel} · {BRAND.series}</div>
    <div style={{ position: "absolute", top: 270, left: 56, width: 968, opacity: progress, transform: `translateY(${(1-progress)*40}px)` }}>
      <div style={{ display: "inline-block", background: TH.accent, color: TH.ink, padding: "16px 24px", borderRadius: TH.radius, fontSize: 30, fontWeight: 700 }}>{label}</div>
      <h1 style={{ fontSize: 94, lineHeight: 1.08, letterSpacing: -3, marginTop: 48 }}>{headline}</h1>
      <div style={{ fontSize: 42, lineHeight: 1.3, color: "#ddd" }}>{detail}</div>
    </div>
    {index === 5 && <div style={{ position: "absolute", left: 56, top: 1000, width: 968, fontSize: 32, lineHeight: 1.45 }}>{LINES.filter(l=>l.id.startsWith("s6") && l.id!=="s6a").map(l=><div key={l.id} style={{opacity:t>=l.beat?1:.25}}>→ {CAPTIONS.find(c=>c.line===l.id)?.text}</div>)}</div>}
    {caption && <div style={{position:"absolute",top:1550,left:56,width:968,background:"#000c",padding:24,boxSizing:"border-box",borderRadius:24,fontSize:44,lineHeight:1.2,textAlign:"center"}}>{caption.text}</div>}
    <div style={{position:"absolute",bottom:54,left:56,fontSize:28,color:TH.accent}}>{BRAND.link}</div>
    <div style={{position:"absolute",bottom:112,left:56,fontSize:24,opacity:.55}}>Вымышленный демонстрационный выпуск</div>
  </div>;
  return <AbsoluteFill style={{ background: TH.ink, justifyContent:"center",alignItems:"center" }}>{vertical ? card : <div style={{width:608,height:1080,position:"relative"}}><div style={{transform:"scale(0.5625)",transformOrigin:"top left"}}>{card}</div></div>}</AbsoluteFill>;
}
