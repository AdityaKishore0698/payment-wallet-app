import { test, expect } from "@playwright/test";
import { addFunds, createUser, loginViaUi, token } from "./helpers";

test.describe("wallet operations", () => {
  test("a user can add funds from the UI", async ({ page, request }) => {
    const user = await createUser(request);
    await loginViaUi(page, user);

    await page.goto("/add-funds");
    await page.getByLabel("Amount").fill("2500");
    await page.getByRole("button", { name: "Add money" }).click();

    await expect(page.getByText(/Added .*2,500/)).toBeVisible();

    await page.goto("/dashboard");
    // 10,000 starting balance + 2,500 = 12,500
    await expect(page.getByText(/12,500/).first()).toBeVisible();
  });

  test("add funds rejects amounts over the per-top-up limit", async ({
    page,
    request,
  }) => {
    const user = await createUser(request);
    await loginViaUi(page, user);

    await page.goto("/add-funds");
    await page.getByLabel("Amount").fill("60000");
    await page.getByRole("button", { name: "Add money" }).click();

    await expect(page.getByText(/at most/i)).toBeVisible();
  });

  test("a P2P transfer moves money between wallets", async ({
    page,
    request,
  }) => {
    const sender = await createUser(request, { firstName: "Sender" });
    const receiver = await createUser(request, { firstName: "Receiver" });
    await addFunds(request, sender, 5000); // 15,000 total

    await loginViaUi(page, sender);
    await page.goto("/transfer");

    await page.getByLabel("Recipient UPI ID").fill(receiver.upiId);
    await expect(page.getByText(/Verified:/)).toBeVisible();

    await page.getByLabel("Amount").fill("1200");
    await page.getByRole("button", { name: "Send money" }).click();

    await expect(page.getByText(/Sent .*1,200/)).toBeVisible();

    // Sender balance: 15,000 - 1,200 = 13,800
    await page.goto("/dashboard");
    await expect(page.getByText(/13,800/).first()).toBeVisible();

    // Sender history shows the debit.
    await page.goto("/history");
    await expect(page.getByText("DEBIT").first()).toBeVisible();
    await expect(page.getByText(/Receiver User/).first()).toBeVisible();

    // Receiver's wallet was credited (verified via API).
    const jwt = await token(request, receiver);
    const walletRes = await request.get(
      `/api/wallets/user/${receiver.userId}`,
      { headers: { Authorization: `Bearer ${jwt}` } },
    );
    expect(Number((await walletRes.json()).balance)).toBe(11200);
  });

  test("transferring to a non-existent UPI ID is blocked", async ({
    page,
    request,
  }) => {
    const user = await createUser(request);
    await loginViaUi(page, user);

    await page.goto("/transfer");
    await page.getByLabel("Recipient UPI ID").fill("ghost999@wallet");

    await expect(page.getByText(/No account found/i)).toBeVisible();
    await expect(page.getByRole("button", { name: "Send money" })).toBeDisabled();
  });

  test("changing password lets the user log in with the new one", async ({
    page,
    request,
  }) => {
    const user = await createUser(request);
    await loginViaUi(page, user);

    await page.goto("/settings");
    await page.getByLabel("Current password").fill(user.password);
    await page.getByLabel("New password").fill("newpassword456");
    await page.getByRole("button", { name: "Update password" }).click();
    await expect(page.getByText(/Password updated/)).toBeVisible();

    await page.getByRole("button", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login$/);

    await page.getByLabel("Email").fill(user.email);
    await page.getByLabel("Password").fill("newpassword456");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
  });
});
