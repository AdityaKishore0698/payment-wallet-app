import { type APIRequestContext, type Page, expect } from "@playwright/test";

export type TestUser = {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  upiId: string;
  userId: string;
};

let counter = 0;

function uniqueSuffix(): string {
  counter += 1;
  const rand = Math.random().toString(36).slice(2, 8);
  return `${Date.now().toString(36)}${counter}${rand}`;
}

/** Create a user directly via the API so UI tests can focus on one flow. */
export async function createUser(
  request: APIRequestContext,
  overrides: Partial<Pick<TestUser, "firstName" | "password">> = {},
): Promise<TestUser> {
  const suffix = uniqueSuffix();
  // Random-ish default name: the backend derives the UPI ID from first_name +
  // a 3-digit number, so identical names across parallel workers risk a
  // unique-constraint collision on upi_id.
  const firstName = overrides.firstName ?? `User${suffix.slice(-5)}`;
  const password = overrides.password ?? "password123";
  const email = `e2e_${suffix}@example.com`;

  const res = await request.post("/api/users/", {
    data: { first_name: firstName, last_name: "User", email, password },
  });
  expect(res.ok(), `register failed: ${res.status()} ${await res.text()}`).toBe(
    true,
  );
  const body = await res.json();

  return {
    firstName,
    lastName: "User",
    email,
    password,
    upiId: body.upi_id,
    userId: body.id,
  };
}

export async function token(
  request: APIRequestContext,
  user: TestUser,
): Promise<string> {
  const res = await request.post("/api/auth/login", {
    form: { username: user.email, password: user.password },
  });
  expect(res.ok()).toBe(true);
  return (await res.json()).access_token;
}

export async function addFunds(
  request: APIRequestContext,
  user: TestUser,
  amount: number,
): Promise<void> {
  const jwt = await token(request, user);
  const walletRes = await request.get(`/api/wallets/user/${user.userId}`, {
    headers: { Authorization: `Bearer ${jwt}` },
  });
  expect(walletRes.ok()).toBe(true);
  const walletId = (await walletRes.json()).id;

  const res = await request.post(`/api/transactions/add_funds/${walletId}`, {
    headers: { Authorization: `Bearer ${jwt}` },
    data: { amount },
  });
  expect(res.ok(), `add_funds failed: ${await res.text()}`).toBe(true);
}

/** Log in through the UI and wait for the dashboard. */
export async function loginViaUi(page: Page, user: TestUser): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
}
