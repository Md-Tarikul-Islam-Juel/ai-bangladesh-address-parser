/**
 * Example 1: Basic Address Extraction
 * 
 * This example demonstrates the basic usage of the address extractor
 * to extract components from a single address.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  // Create extractor instance
  const extractor = new AddressExtractor();

  // Example 1: Simple address
  console.log("=== Example 1: Simple Address ===");
  const address1 = "House 12, Road 5, Mirpur, Dhaka-1216";
  const result1 = await extractor.extract(address1);

  console.log("Input:", address1);
  console.log("Extracted Components:");
  console.log(`  House Number: ${result1.components.house_number || 'N/A'}`);
  console.log(`  Road: ${result1.components.road || 'N/A'}`);
  console.log(`  Area: ${result1.components.area || 'N/A'}`);
  console.log(`  District: ${result1.components.district || 'N/A'}`);
  console.log(`  Postal Code: ${result1.components.postal_code || 'N/A'}`);
  console.log(`  Confidence: ${(result1.overall_confidence * 100).toFixed(1)}%`);
  console.log(`  Extraction Time: ${result1.extraction_time_ms.toFixed(2)}ms`);
  console.log();

  // Example 2: Complex address
  console.log("=== Example 2: Complex Address ===");
  const address2 = '1152/C "Greenhouse", House# 45, Road# 08, Shapla Residential Area, Halishahar, Chittagong-4219';
  const result2 = await extractor.extract(address2);

  console.log("Input:", address2);
  console.log("Extracted Components:");
  Object.entries(result2.components).forEach(([key, value]) => {
    if (value) {
      console.log(`  ${key}: ${value}`);
    }
  });
  console.log(`  Confidence: ${(result2.overall_confidence * 100).toFixed(1)}%`);
  console.log();

  // Example 3: Address with flat/floor
  console.log("=== Example 3: Address with Flat/Floor ===");
  const address3 = "Flat A-3, Building 7, Bashundhara R/A, Dhaka";
  const result3 = await extractor.extract(address3);

  console.log("Input:", address3);
  console.log("Extracted Components:");
  console.log(`  Flat Number: ${result3.components.flat_number || 'N/A'}`);
  console.log(`  Area: ${result3.components.area || 'N/A'}`);
  console.log(`  District: ${result3.components.district || 'N/A'}`);
  console.log(`  Postal Code: ${result3.components.postal_code || 'N/A'}`);
  console.log();

  // Example 4: Minimal address
  console.log("=== Example 4: Minimal Address ===");
  const address4 = "Banani, Dhaka";
  const result4 = await extractor.extract(address4);

  console.log("Input:", address4);
  console.log("Extracted Components:");
  console.log(`  Area: ${result4.components.area || 'N/A'}`);
  console.log(`  District: ${result4.components.district || 'N/A'}`);
  console.log(`  Postal Code: ${result4.components.postal_code || 'N/A'}`);
  console.log();
}

main().catch(console.error);
