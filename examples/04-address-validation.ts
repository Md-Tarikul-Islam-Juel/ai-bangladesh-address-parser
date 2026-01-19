/**
 * Example 4: Address Validation
 * 
 * This example demonstrates validating addresses for completeness
 * and checking for missing components.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  // Example 1: Complete address
  console.log("=== Example 1: Complete Address ===");
  const address1 = "House 12, Road 5, Mirpur, Dhaka-1216";
  const validation1 = await extractor.validate(address1);

  console.log("Address:", address1);
  console.log("Is Valid:", validation1.is_valid);
  console.log("Completeness:", `${(validation1.completeness * 100).toFixed(1)}%`);
  console.log("Score:", validation1.score.toFixed(3));
  console.log("Missing Components:", validation1.missing.length > 0 ? validation1.missing.join(", ") : "None");
  console.log("Invalid Components:", validation1.invalid.length > 0 ? validation1.invalid.join(", ") : "None");
  console.log();

  // Example 2: Incomplete address
  console.log("=== Example 2: Incomplete Address ===");
  const address2 = "Mirpur, Dhaka";
  const validation2 = await extractor.validate(address2);

  console.log("Address:", address2);
  console.log("Is Valid:", validation2.is_valid);
  console.log("Completeness:", `${(validation2.completeness * 100).toFixed(1)}%`);
  console.log("Missing Components:", validation2.missing.length > 0 ? validation2.missing.join(", ") : "None");
  console.log();

  // Example 3: Strict validation with custom requirements
  console.log("=== Example 3: Strict Validation ===");
  const address3 = "House 12, Road 5, Mirpur, Dhaka";
  const validation3 = await extractor.validate(address3, [
    'district',
    'area',
    'postal_code',
    'house_number'
  ]);

  console.log("Address:", address3);
  console.log("Required:", ['district', 'area', 'postal_code', 'house_number'].join(", "));
  console.log("Is Valid:", validation3.is_valid);
  console.log("Missing Required:", validation3.missing.length > 0 ? validation3.missing.join(", ") : "None");
  console.log();

  // Example 4: Validation for e-commerce checkout
  console.log("=== Example 4: E-commerce Checkout Validation ===");
  const checkoutAddresses = [
    "House 12, Road 5, Mirpur, Dhaka-1216",  // Complete
    "Banani, Dhaka",                          // Missing postal
    "House 45, Chittagong",                   // Missing area and postal
  ];

  for (const addr of checkoutAddresses) {
    const validation = await extractor.validate(addr, ['district', 'area', 'postal_code']);
    
    console.log(`\nAddress: ${addr}`);
    if (validation.is_valid) {
      console.log("✅ Valid for checkout");
    } else {
      console.log("❌ Invalid - Missing:", validation.missing.join(", "));
    }
  }
}

main().catch(console.error);
