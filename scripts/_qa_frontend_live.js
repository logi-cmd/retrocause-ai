const { chromium } = require("playwright");

const FRONTEND_URL = process.env.RETROCAUSE_FRONTEND_URL || "http://localhost:3005";
const DEFAULT_QUERY =
  "\u7f8e\u56fd\u4e3a\u4ec0\u4e48\u4f1a\u63a8\u51fa\u65b0\u7684\u534a\u5bfc\u4f53\u51fa\u53e3\u7ba1\u5236\uff1f";
const SCENARIOS = {
  bitcoin:
    "\u6bd4\u7279\u5e01\u4eca\u65e5\u4ef7\u683c\u4e3a\u4f55\u8df3\u6c34",
  semiconductor: DEFAULT_QUERY,
};
const QUERY =
  process.env.RETROCAUSE_QA_QUERY ||
  SCENARIOS[process.env.RETROCAUSE_QA_SCENARIO || ""] ||
  DEFAULT_QUERY;
const API_KEY = process.env.RETROCAUSE_OPENROUTER_KEY || "";
const MIN_CARDS = Number(process.env.RETROCAUSE_QA_MIN_CARDS || "6");
const EXPECTED_PATTERN = process.env.RETROCAUSE_QA_EXPECTED_PATTERN
  ? new RegExp(process.env.RETROCAUSE_QA_EXPECTED_PATTERN, "i")
  : null;

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function textOf(locator) {
  if ((await locator.count()) === 0) return "";
  return (await locator.first().textContent()) || "";
}

async function clickIfPresent(locator) {
  if ((await locator.count()) === 0) return false;
  await locator.first().click();
  return true;
}

function looksLocalized(text) {
  const hasCjk = /[\u4e00-\u9fff]/.test(text);
  const englishTokens = text.match(/[A-Za-z]{4,}/g) || [];
  return hasCjk && englishTokens.length <= 2;
}

async function main() {
  assert(API_KEY, "RETROCAUSE_OPENROUTER_KEY is required for live frontend QA");

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors.push(msg.text());
    }
  });
  page.on("pageerror", (err) => errors.push(err.message));

  await page.goto(FRONTEND_URL, { waitUntil: "networkidle", timeout: 60000 });
  await page.locator("textarea").first().fill(QUERY);
  await page.locator("input[type='password']").first().fill(API_KEY);
  await page.getByRole("button", { name: /\u5f00\u59cb\u5206\u6790|Start Analysis/ }).click();

  await page.waitForFunction(
    () => document.body.innerText.includes("Live"),
    null,
    { timeout: 420000 }
  );

  const bodyAfterLive = await page.locator("body").innerText();
  assert(!bodyAfterLive.includes("demo fallback"), "Live QA fell back to demo fallback");
  assert(!bodyAfterLive.includes("demo \u56de\u9000"), "Live QA fell back to demo fallback");
  assert(bodyAfterLive.includes("Live"), "Live QA did not surface a Live status");

  const cards = page.locator(".sticky-card");
  const cardCount = await cards.count();
  assert(
    cardCount >= MIN_CARDS,
    `Expected at least ${MIN_CARDS} graph cards for live result, got ${cardCount}`
  );

  const firstCardTextZh = await textOf(cards.first());
  assert(
    looksLocalized(firstCardTextZh),
    `Chinese graph card did not look localized: ${firstCardTextZh}`
  );
  if (EXPECTED_PATTERN) {
    assert(
      EXPECTED_PATTERN.test(bodyAfterLive),
      `Live result did not include expected pattern ${EXPECTED_PATTERN}: ${bodyAfterLive.slice(0, 800)}`
    );
  }

  await cards.first().click();
  await page.waitForTimeout(300);

  const chainButton = page
    .locator("button")
    .filter({ hasText: /%/ })
    .filter({ hasNotText: /Start Analysis|\u5f00\u59cb\u5206\u6790|Live|Demo/ });
  const chainButtonCount = await chainButton.count();
  if (chainButtonCount > 0) {
    await chainButton.first().click();
    await page.waitForTimeout(500);
  }

  const beforeToggleCardCount = await cards.count();
  const beforeToggleText = await page.locator("body").innerText();
  await page.getByRole("button", { name: /\u4e2d|EN/ }).first().click();
  await page.waitForTimeout(700);

  const afterToggleText = await page.locator("body").innerText();
  const afterToggleCardCount = await cards.count();
  assert(afterToggleCardCount === beforeToggleCardCount, "Language toggle changed graph card count");
  assert(afterToggleText.includes("Live"), "Language toggle reset live result state");
  assert(afterToggleText !== beforeToggleText, "Language toggle did not visibly switch locale");

  const clickedAfterToggle = await clickIfPresent(
    page
      .locator("button")
      .filter({ hasText: /%/ })
      .filter({ hasNotText: /Start Analysis|\u5f00\u59cb\u5206\u6790|Live|Demo/ })
  );
  if (clickedAfterToggle) {
    await page.waitForTimeout(500);
  }

  const cardsAfterInteractions = await cards.count();
  assert(
    cardsAfterInteractions >= MIN_CARDS,
    `Expected graph cards to remain after chain interactions, got ${cardsAfterInteractions}`
  );

  if (errors.length > 0) {
    throw new Error(`Console/page errors: ${errors.join(" | ")}`);
  }

  console.log(
    JSON.stringify({
      ok: true,
      query: QUERY,
      cardCount,
      chainButtonCount,
      beforeToggleCardCount,
      afterToggleCardCount,
    })
  );
  await browser.close();
}

main().catch(async (err) => {
  console.error(err);
  process.exit(1);
});
