import { test, expect } from '@playwright/test';

test('VeraRecording_manualcrawl Recorded Session', async ({ page }) => {
  await page.goto('/');
  await page.locator('id("HyperLink1")/IMG[1]').click();
  await page.locator('#AccountLink').click();
  await page.locator('[name="uid"]').fill('test');
  await page.locator('[name="passw"]').fill('test');
  await page.locator('[name="btnSubmit"]').click();
  await page.locator('id("MenuHyperLink6")').click();
});