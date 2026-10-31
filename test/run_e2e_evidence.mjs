/**
 * Automated End-to-End Verification and Screenshot Generator for KAWACH.
 * Uses puppeteer-core with local Chrome to execute UI scenarios live.
 */

import puppeteer from "../frontend/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const BASE_URL = "http://127.0.0.1:5173";
const EVIDENCE_DIR = "c:\\KAWACH\\test\\evidence";

const executablePath = fs.existsSync(CHROME_PATH) ? CHROME_PATH : EDGE_PATH;

if (!fs.existsSync(EVIDENCE_DIR)) {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

async function run() {
  console.log(`Starting headless browser with: ${executablePath}`);
  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
  });

  const page = await browser.newPage();

  // 1. Laptop view
  await page.setViewport({ width: 1280, height: 900 });
  console.log(`Navigating to ${BASE_URL}...`);
  await page.goto(BASE_URL, { waitUntil: "networkidle0", timeout: 15000 });

  // Wait for backend connection indicator
  await page.waitForFunction(
    () => document.body.innerText.includes("Backend connected"),
    { timeout: 10000 }
  );
  console.log("Verified: Backend connected status visible on UI.");

  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "dashboard_laptop.png"),
    fullPage: true,
  });
  console.log("Saved dashboard_laptop.png");

  // 2. Mobile view verification
  await page.setViewport({ width: 375, height: 812 });
  await page.waitForTimeout ? page.waitForTimeout(500) : new Promise((r) => setTimeout(r, 500));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "dashboard_mobile.png"),
    fullPage: true,
  });
  console.log("Saved dashboard_mobile.png (narrow mobile layout)");

  // Restore laptop view
  await page.setViewport({ width: 1280, height: 900 });
  await new Promise((r) => setTimeout(r, 500));

  // 3. Navigate to Demo Scenarios page
  const navButtons = await page.$$("nav button");
  let demoNav = null;
  for (const btn of navButtons) {
    const text = await (await btn.getProperty("innerText")).jsonValue();
    if (text.includes("Demo Scenarios")) {
      demoNav = btn;
      break;
    }
  }
  if (demoNav) {
    await demoNav.click();
    await new Promise((r) => setTimeout(r, 800));
  }

  console.log("Navigated to Demo Scenarios page.");

  // Helper to click buttons by text inside container
  async function clickButtonWithText(txt) {
    await new Promise((r) => setTimeout(r, 600));
    const buttons = await page.$$("button");
    for (const b of buttons) {
      const text = await (await b.getProperty("innerText")).jsonValue();
      if (text && text.includes(txt)) {
        await b.evaluate((el) => el.scrollIntoView({ block: "center" }));
        await new Promise((r) => setTimeout(r, 300));
        await b.click();
        console.log(`Clicked button: "${txt}"`);
        return true;
      }
    }
    console.warn(`Could not find button matching: "${txt}"`);
    return false;
  }

  // Helper to wait for text
  async function waitForText(txt, timeout = 8000) {
    await page.waitForFunction(
      (t) => document.body.innerText.includes(t),
      { timeout },
      txt
    );
  }

  // Demo 1: Legitimate Task Execution
  console.log("Running Demo 1 (Legitimate Task Execution)...");
  await clickButtonWithText("Run Demo 1");
  await waitForText("Step 1: document_reader.read");
  await waitForText("Step 2: file_manager.list");
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo1_legitimate.png"),
    fullPage: false,
  });
  console.log("Saved demo1_legitimate.png");

  // Demo 2: EchoLeak-Inspired Prompt Injection
  console.log("Running Demo 2 (EchoLeak-Inspired Prompt Injection)...");
  await clickButtonWithText("Run Demo 2");
  await waitForText("Step 2: document_reader.read");
  await waitForText("Step 3: email_sender.send");
  await waitForText("RESOURCE_SECRET");
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo2_echoLeak_prompt_injection.png"),
    fullPage: false,
  });
  console.log("Saved demo2_echoLeak_prompt_injection.png");

  // Demo 3: Sensitive Data Access
  console.log("Running Demo 3 (Sensitive-Data Access Attempt)...");
  await clickButtonWithText("Run Demo 3");
  await waitForText("Step 4: document_reader.read");
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo3_sensitive_data.png"),
    fullPage: false,
  });
  console.log("Saved demo3_sensitive_data.png");

  // Demo 4: Tool Permission Violation
  console.log("Running Demo 4 (Tool Permission Violation)...");
  await clickButtonWithText("Run Demo 4");
  await waitForText("Step 2: file_manager.delete");
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo4_tool_permission_violation.png"),
    fullPage: false,
  });
  console.log("Saved demo4_tool_permission_violation.png");

  // Demo 5: Human Approval
  console.log("Running Demo 5 (Human Approval Workflow)...");
  await clickButtonWithText("Run Demo 5");
  await waitForText("Human Decision Required");
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo5_approval_pending.png"),
    fullPage: false,
  });
  console.log("Saved demo5_approval_pending.png");

  // Branch A: Reject
  console.log("Testing Demo 5 Branch A (Reject)...");
  await clickButtonWithText("Branch A: Reject Action");
  await waitForText("Zero mock emails sent");
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo5_reject_branch.png"),
    fullPage: false,
  });
  console.log("Saved demo5_reject_branch.png");

  // Run Demo 5 again for Approve branch
  await clickButtonWithText("Run Demo 5");
  await waitForText("Human Decision Required");
  await new Promise((r) => setTimeout(r, 800));

  // Branch B: Approve
  console.log("Testing Demo 5 Branch B (Approve)...");
  await clickButtonWithText("Branch B: Approve Action");
  await waitForText("Exactly 1 mock email sent");
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo5_approve_branch.png"),
    fullPage: false,
  });
  console.log("Saved demo5_approve_branch.png");

  // Replay Attack Test
  console.log("Testing Demo 5 Replay Attack Defense...");
  await clickButtonWithText("Test Replay Defense");
  await waitForText("already approved and cannot be re-processed");
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo5_replay_blocked.png"),
    fullPage: false,
  });
  console.log("Saved demo5_replay_blocked.png");

  // Demo 6: Fail-Closed Behaviour
  console.log("Running Demo 6 (Fail-Closed Unknown Tool)...");
  await clickButtonWithText("Run Demo 6");
  await waitForText("Step 1: shell_command_executor.exec");
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo6_unknown_tool.png"),
    fullPage: false,
  });
  console.log("Saved demo6_unknown_tool.png");

  // Select Policy Error Hook (Sub-case 5)
  console.log("Testing Demo 6 Sub-case 5 (Simulated Policy Engine Crash Hook)...");
  await clickButtonWithText("5: Policy Engine Failure Hook");
  await new Promise((r) => setTimeout(r, 300));
  await clickButtonWithText("Run Demo 6");
  await waitForText("POLICY_ERROR");
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "demo6_policy_error_fail_closed.png"),
    fullPage: false,
  });
  console.log("Saved demo6_policy_error_fail_closed.png");

  // 4. Approvals Page
  for (const btn of await page.$$("nav button")) {
    const text = await (await btn.getProperty("innerText")).jsonValue();
    if (text.includes("Approvals")) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "approvals_history.png"),
    fullPage: true,
  });
  console.log("Saved approvals_history.png");

  // 5. Audit Logs Page
  for (const btn of await page.$$("nav button")) {
    const text = await (await btn.getProperty("innerText")).jsonValue();
    if (text.includes("Audit Logs")) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "audit_logs.png"),
    fullPage: true,
  });
  console.log("Saved audit_logs.png");

  // 6. Agent Console Page
  for (const btn of await page.$$("nav button")) {
    const text = await (await btn.getProperty("innerText")).jsonValue();
    if (text.includes("Agent Console")) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1000));
  await clickButtonWithText("Submit Task to Agent");
  await waitForText("OVERALL DECISION");
  await new Promise((r) => setTimeout(r, 1000));
  await page.screenshot({
    path: path.join(EVIDENCE_DIR, "agent_console.png"),
    fullPage: true,
  });
  console.log("Saved agent_console.png");

  await browser.close();
  console.log("\nAll end-to-end browser verifications completed successfully!");
}

run().catch((err) => {
  console.error("End-to-end verification encountered error:", err);
  process.exit(1);
});
