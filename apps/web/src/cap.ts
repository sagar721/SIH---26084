// CAP 1.2 draft for an approved advisory (PRD F12). Always status=Exercise with the research-prototype disclaimer.
import type { DraftAlert } from "./types";

export const DISCLAIMER = "Research prototype — not an official IMD warning. Replay of observed data.";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

export function capXml(a: DraftAlert, issueUtc: string, event: string, modelVersion: string): string {
  const sent = issueUtc.replace(/Z$/, "+00:00");
  const expires = new Date(new Date(issueUtc).getTime() + (a.lead_min + 60) * 60000).toISOString().replace(/\.000Z$/, "+00:00");
  const id = `sih26084-${event}-${a.alert_id.replace(/[^A-Za-z0-9]/g, "-")}`;
  return `<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>${esc(id)}</identifier>
  <sender>sih26084-prototype@example.invalid</sender>
  <sent>${sent}</sent>
  <status>Exercise</status>
  <msgType>Alert</msgType>
  <scope>Private</scope>
  <note>${esc(DISCLAIMER)} Source prediction: ${esc(a.prediction_id)} (model ${esc(modelVersion)}).</note>
  <info>
    <category>Met</category>
    <event>Deep convection (cloud top below 235 K)</event>
    <urgency>Expected</urgency>
    <severity>Moderate</severity>
    <certainty>Possible</certainty>
    <expires>${expires}</expires>
    <senderName>SIH26084 student research prototype</senderName>
    <headline>EXERCISE: deep convection probability ${a.p_max.toFixed(2)} near ${esc(a.place)} within ${a.lead_min} min</headline>
    <description>Calibrated ML probability of cloud-top brightness temperature below 235 K within 10 km of ${esc(a.place)} at +${a.lead_min} min is ${a.p_max.toFixed(2)} (draft rule: p &gt;= 0.5). This is a probability, not a guaranteed outcome. No hail, lightning or rainfall forecast is implied.</description>
    <parameter><valueName>prediction_id</valueName><value>${esc(a.prediction_id)}</value></parameter>
    <area>
      <areaDesc>${esc(a.place)} (10 km)</areaDesc>
      <circle>${a.lat.toFixed(4)},${a.lon.toFixed(4)} 10</circle>
    </area>
  </info>
</alert>`;
}
