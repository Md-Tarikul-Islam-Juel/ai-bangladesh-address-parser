/**
 * Example 5: Address Formatting
 * 
 * This example demonstrates formatting addresses into
 * different standardized formats for various use cases.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  const address = "House 12, Road 5, Mirpur, Dhaka-1216";

  console.log("=== Address Formatting Examples ===");
  console.log("Original Address:", address);
  console.log();

  // Example 1: Full format (default)
  console.log("=== 1. Full Format (Default) ===");
  const full = await extractor.format(address);
  console.log("Formatted:", full);
  console.log("Use Case: Complete address display");
  console.log();

  // Example 2: Short format
  console.log("=== 2. Short Format ===");
  const short = await extractor.format(address, { style: 'short' });
  console.log("Formatted:", short);
  console.log("Use Case: Compact display, UI cards");
  console.log();

  // Example 3: Postal format
  console.log("=== 3. Postal Format ===");
  const postal = await extractor.format(address, { style: 'postal' });
  console.log("Formatted:", postal);
  console.log("Use Case: Postal services, shipping labels");
  console.log();

  // Example 4: Minimal format
  console.log("=== 4. Minimal Format ===");
  const minimal = await extractor.format(address, { style: 'minimal' });
  console.log("Formatted:", minimal);
  console.log("Use Case: Quick reference, search results");
  console.log();

  // Example 5: Custom separator
  console.log("=== 5. Custom Separator ===");
  const custom = await extractor.format(address, {
    style: 'full',
    separator: ' | ',
    includePostal: true
  });
  console.log("Formatted:", custom);
  console.log("Use Case: Database storage, CSV export");
  console.log();

  // Example 6: Without postal code
  console.log("=== 6. Without Postal Code ===");
  const noPostal = await extractor.format(address, {
    style: 'full',
    includePostal: false
  });
  console.log("Formatted:", noPostal);
  console.log("Use Case: When postal code is not needed");
  console.log();

  // Example 7: Formatting for shipping labels
  console.log("=== 7. Shipping Label Format ===");
  const shippingAddresses = [
    "House 12, Road 5, Mirpur, Dhaka-1216",
    "Flat A-3, Building 7, Bashundhara R/A, Dhaka",
    "Banani, Dhaka-1213",
  ];

  console.log("Shipping Labels:");
  for (const addr of shippingAddresses) {
    const formatted = await extractor.format(addr, { style: 'full' });
    console.log(`  ${formatted}`);
  }
  console.log();

  // Example 8: Formatting for database storage
  console.log("=== 8. Database Storage Format ===");
  const dbFormatted = await extractor.format(address, {
    style: 'full',
    separator: ',',
    includePostal: true
  });
  console.log("Formatted:", dbFormatted);
  console.log("Use Case: Storing in database as single string");
}

main().catch(console.error);
