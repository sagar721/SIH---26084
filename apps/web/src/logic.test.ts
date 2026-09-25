import { describe, expect, it } from "vitest";
import { decodeBT, decodeP, irColor, pBin, pColor, NODATA } from "./colors";
import { capXml, DISCLAIMER } from "./cap";
import { addMinutes, destination, issueKey, leadLabel, utcIst } from "./format";

describe("bundle decoding", () => {
  it("decodes BT and probability codes and no-data", () => {
    expect(decodeBT(75)).toBe(235);
    expect(decodeBT(NODATA)).toBeNull();
    expect(decodeP(125)).toBeCloseTo(0.5);
    expect(decodeP(NODATA)).toBeNull();
  });
});

describe("colour scales", () => {
  it("probability bins follow the 0.1/0.3/0.5/0.7/0.9 spec and hide values below the threshold", () => {
    expect(pBin(0.05)).toBe(-1);
    expect(pBin(0.1)).toBe(0);
    expect(pBin(0.55)).toBe(2);
    expect(pBin(0.95)).toBe(4);
    expect(pColor(0.4, 0.5)[3]).toBe(0);
    expect(pColor(0.6, 0.5)[3]).toBeGreaterThan(0);
  });
  it("IR scale is transparent when warm and opaque when cold", () => {
    expect(irColor(315)[3]).toBe(0);
    expect(irColor(210)[3]).toBeGreaterThan(200);
  });
});

describe("CAP exercise alert", () => {
  const a = { alert_id: "ml-v0/E8/20260514T0900Z/L60#Ambala", place: "Ambala", lat: 30.38, lon: 76.78, lead_min: 60, p_max: 0.71, prediction_id: "ml-v0/E8/20260514T0900Z/L60" };
  const xml = capXml(a, "2026-05-14T09:00:00Z", "E8_20260514", "ml-v0");
  it("is always an Exercise with the disclaimer and the source prediction id", () => {
    expect(xml).toContain("<status>Exercise</status>");
    expect(xml).toContain(DISCLAIMER);
    expect(xml).toContain("ml-v0/E8/20260514T0900Z/L60");
    expect(xml).toContain("<circle>30.3800,76.7800 10</circle>");
    expect(xml).not.toContain("<status>Actual</status>");
    expect(xml).toMatch(/<identifier>[^<]*Ambala<\/identifier>/);   // one identifier per place-level advisory
  });
});

describe("format helpers", () => {
  it("converts UTC to IST and formats leads", () => {
    expect(utcIst("2026-05-14T09:00:00Z")).toEqual({ utc: "09:00", ist: "14:30", date: "2026-05-14" });
    expect(addMinutes("2026-05-14T23:30:00Z", 60)).toBe("2026-05-15T00:30:00Z");
    expect(leadLabel(120)).toBe("T+2h");
    expect(issueKey("2026-05-14T08:00:00Z")).toBe("2026-05-14 08:00:00");
  });
  it("destination moves east for bearing 90", () => {
    const [lon, lat] = destination(78, 30, 90, 100);
    expect(lon).toBeGreaterThan(78.9);
    expect(Math.abs(lat - 30)).toBeLessThan(0.05);
  });
});
