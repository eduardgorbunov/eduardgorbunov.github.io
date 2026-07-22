#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const baseUrl = process.env.SITE_PREVIEW_URL || "http://127.0.0.1:8000";
const manifestPath = path.join(root, "automation", "changed-publications.json");
const outputDir = path.resolve(process.env.SCREENSHOT_OUTPUT || path.join(root, ".automation-screenshots"));

function readChangedIds() {
  if (!fs.existsSync(manifestPath)) return [];
  const payload = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  return Array.isArray(payload.publicationIds) ? payload.publicationIds : [];
}

function safeName(value) {
  return value.replace(/[^a-z0-9_-]+/gi, "-").replace(/^-|-$/g, "");
}

async function captureViewport(browser, config, publicationIds, results) {
  const page = await browser.newPage({
    viewport: config.viewport,
    deviceScaleFactor: 1,
    colorScheme: "light",
    reducedMotion: "reduce",
  });
  await page.goto(`${baseUrl}/publications.html`, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForSelector("#publication-list .eg-publication-card", { timeout: 20000 });
  await page.evaluate(async () => {
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
  });

  const viewportOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  if (viewportOverflow) {
    throw new Error(`${config.name} preview has horizontal page overflow`);
  }

  const ids = publicationIds.length ? publicationIds : ["publication-overview", "publication-filters"];
  for (const id of ids) {
    if (!/^[A-Za-z][A-Za-z0-9_-]*$/.test(id)) {
      throw new Error(`Unsafe element id in screenshot manifest: ${id}`);
    }
    const selector = `#${id}`;
    const locator = page.locator(selector);
    if ((await locator.count()) !== 1) {
      throw new Error(`Expected exactly one element for ${selector}`);
    }
    await locator.scrollIntoViewIfNeeded();
    const box = await locator.boundingBox();
    if (!box || box.width < 20 || box.height < 20) {
      throw new Error(`${selector} is blank or incorrectly sized`);
    }
    const filename = `${config.name}-${safeName(id)}.png`;
    await locator.screenshot({ path: path.join(outputDir, filename), animations: "disabled" });
    results.push({ viewport: config.name, id, filename, width: Math.round(box.width), height: Math.round(box.height) });
  }
  await page.close();
}

(async () => {
  fs.mkdirSync(outputDir, { recursive: true });
  const publicationIds = readChangedIds();
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    await captureViewport(
      browser,
      { name: "desktop", viewport: { width: 1440, height: 1000 } },
      publicationIds,
      results,
    );
    await captureViewport(
      browser,
      { name: "mobile", viewport: { width: 390, height: 844 } },
      publicationIds,
      results,
    );
  } finally {
    await browser.close();
  }
  fs.writeFileSync(
    path.join(outputDir, "manifest.json"),
    `${JSON.stringify({ generatedAt: new Date().toISOString(), baseUrl, screenshots: results }, null, 2)}\n`,
  );
  process.stdout.write(`Captured ${results.length} publication review screenshots.\n`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
