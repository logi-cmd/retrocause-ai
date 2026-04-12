const { chromium } = require("playwright");

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });
  page.on("pageerror", (err) => errors.push(err.message));

  await page.goto("http://localhost:3005", { waitUntil: "networkidle", timeout: 30000 });
  await page.getByRole("button", { name: /中|EN/ }).click();
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: /中|EN/ }).click();
  await page.waitForTimeout(500);

  const stickyCount = await page.locator(".sticky-card").count();
  if (stickyCount < 1) {
    throw new Error(`Expected sticky cards, found ${stickyCount}`);
  }
  await page.locator(".sticky-card").first().click();
  await page.waitForTimeout(300);

  const alternativeButtons = page.locator("button", { hasText: /Confidence|置信|%/ });
  const altCount = await alternativeButtons.count();
  if (altCount > 0) {
    await alternativeButtons.first().click();
    await page.waitForTimeout(300);
  }

  if (errors.length > 0) {
    throw new Error(`Console/page errors: ${errors.join(" | ")}`);
  }

  console.log(JSON.stringify({ ok: true, stickyCount, altCount }));
  await browser.close();
}

main().catch(async (err) => {
  console.error(err);
  process.exit(1);
});
