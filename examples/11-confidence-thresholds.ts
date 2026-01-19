/**
 * Example 11: Confidence Thresholds Configuration
 * 
 * This example demonstrates setting and using
 * custom confidence thresholds for components.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  // Example 1: Default thresholds
  console.log("=== Example 1: Default Thresholds ===");
  const extractor1 = new AddressExtractor();
  const defaultThresholds = extractor1.getConfidenceThresholds();

  console.log("Default Thresholds:");
  if (defaultThresholds) {
    Object.entries(defaultThresholds).forEach(([component, threshold]: [string, any]) => {
      console.log(`  ${component}: ${(threshold * 100).toFixed(0)}%`);
    });
  } else {
    console.log("  Using system defaults");
  }
  console.log();

  const result1 = await extractor1.extract("House 12, Road 5, Mirpur, Dhaka-1216");
  console.log("Extracted with default thresholds:");
  console.log("  Components:", Object.keys(result1.components).filter(k => result1.components[k as keyof typeof result1.components]));
  console.log("  Confidence:", `${(result1.overall_confidence * 100).toFixed(1)}%`);
  console.log();

  // Example 2: Strict thresholds
  console.log("=== Example 2: Strict Thresholds ===");
  const extractor2 = new AddressExtractor();
  extractor2.setConfidenceThresholds({
    house_number: 0.90,
    postal_code: 0.95,
    district: 0.90,
    area: 0.85,
    road: 0.85,
  });

  console.log("Strict Thresholds Set:");
  const strictThresholds = extractor2.getConfidenceThresholds();
  if (strictThresholds) {
    Object.entries(strictThresholds).forEach(([component, threshold]: [string, any]) => {
      console.log(`  ${component}: ${(threshold * 100).toFixed(0)}%`);
    });
  }
  console.log();

  const result2 = await extractor2.extract("House 12, Road 5, Mirpur, Dhaka-1216");
  console.log("Extracted with strict thresholds:");
  console.log("  Components:", Object.keys(result2.components).filter(k => result2.components[k as keyof typeof result2.components]));
  console.log("  Confidence:", `${(result2.overall_confidence * 100).toFixed(1)}%`);
  console.log("  Note: Only high-confidence components are included");
  console.log();

  // Example 3: Lenient thresholds
  console.log("=== Example 3: Lenient Thresholds ===");
  const extractor3 = new AddressExtractor();
  extractor3.setConfidenceThresholds({
    house_number: 0.60,
    postal_code: 0.70,
    area: 0.55,
    district: 0.65,
    road: 0.60,
  });

  console.log("Lenient Thresholds Set:");
  const lenientThresholds = extractor3.getConfidenceThresholds();
  if (lenientThresholds) {
    Object.entries(lenientThresholds).forEach(([component, threshold]: [string, any]) => {
      console.log(`  ${component}: ${(threshold * 100).toFixed(0)}%`);
    });
  }
  console.log();

  const result3 = await extractor3.extract("House 12, Road 5, Mirpur, Dhaka-1216");
  console.log("Extracted with lenient thresholds:");
  console.log("  Components:", Object.keys(result3.components).filter(k => result3.components[k as keyof typeof result3.components]));
  console.log("  Confidence:", `${(result3.overall_confidence * 100).toFixed(1)}%`);
  console.log("  Note: More components included, even with lower confidence");
  console.log();

  // Example 4: Custom thresholds for specific use case
  console.log("=== Example 4: Custom Thresholds for E-commerce ===");
  const extractor4 = new AddressExtractor();
  extractor4.setConfidenceThresholds({
    house_number: 0.75,    // Important for delivery
    postal_code: 0.85,      // Critical for shipping
    district: 0.80,         // Important for routing
    area: 0.70,             // Helpful for delivery
    road: 0.70,             // Nice to have
  });

  console.log("E-commerce Thresholds:");
  const ecommerceThresholds = extractor4.getConfidenceThresholds();
  if (ecommerceThresholds) {
    Object.entries(ecommerceThresholds).forEach(([component, threshold]: [string, any]) => {
      console.log(`  ${component}: ${(threshold * 100).toFixed(0)}%`);
    });
  }
  console.log();

  const addresses = [
    "House 12, Road 5, Mirpur, Dhaka-1216",
    "Banani, Dhaka",
    "House 45, Chittagong",
  ];

  console.log("Validating addresses for checkout:");
  for (const address of addresses) {
    const result = await extractor4.extract(address);
    const hasRequired = result.components.postal_code && result.components.district;
    
    console.log(`\n  "${address}"`);
    console.log(`    Postal Code: ${result.components.postal_code || 'Missing'}`);
    console.log(`    District: ${result.components.district || 'Missing'}`);
    console.log(`    Valid for Checkout: ${hasRequired ? '✅ Yes' : '❌ No'}`);
  }
  console.log();

  // Example 5: Comparing results with different thresholds
  console.log("=== Example 5: Comparing Different Thresholds ===");
  const testAddress = "House 12, Road 5, Mirpur, Dhaka-1216";

  const extractors = [
    { name: "Default", extractor: new AddressExtractor() },
    { name: "Strict", extractor: (() => {
      const e = new AddressExtractor();
      e.setConfidenceThresholds({ house_number: 0.90, postal_code: 0.95, district: 0.90, area: 0.85 });
      return e;
    })() },
    { name: "Lenient", extractor: (() => {
      const e = new AddressExtractor();
      e.setConfidenceThresholds({ house_number: 0.60, postal_code: 0.70, district: 0.65, area: 0.55 });
      return e;
    })() },
  ];

  console.log(`Testing address: "${testAddress}"\n`);
  for (const { name, extractor } of extractors) {
    const result = await extractor.extract(testAddress);
    const componentCount = Object.values(result.components).filter(v => v).length;
    
    console.log(`${name} Thresholds:`);
    console.log(`  Components Extracted: ${componentCount}`);
    console.log(`  Confidence: ${(result.overall_confidence * 100).toFixed(1)}%`);
    console.log();
  }
}

main().catch(console.error);
