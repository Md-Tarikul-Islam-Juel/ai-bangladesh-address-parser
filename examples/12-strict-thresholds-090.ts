/**
 * Example 12: Strict Confidence Thresholds (0.90 for all components)
 * 
 * This example demonstrates setting all confidence thresholds to 0.90
 * for high-precision extraction - only accepting components with 90%+ confidence.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  // Set all confidence thresholds to 0.90 (90%)
  extractor.setConfidenceThresholds({
    house_number: 0.90,    // Only accept house numbers with 90%+ confidence
    road: 0.90,            // Only accept roads with 90%+ confidence
    area: 0.90,            // Only accept areas with 90%+ confidence
    district: 0.90,        // Only accept districts with 90%+ confidence
    division: 0.90,        // Only accept divisions with 90%+ confidence
    postal_code: 0.90,     // Only accept postal codes with 90%+ confidence
    flat_number: 0.90,     // Only accept flat numbers with 90%+ confidence
    floor_number: 0.90,    // Only accept floor numbers with 90%+ confidence
    block_number: 0.90     // Only accept block numbers with 90%+ confidence
  });

  // Get current thresholds to verify
  const currentThresholds = extractor.getConfidenceThresholds();
  console.log("=== Current Confidence Thresholds ===");
  if (currentThresholds) {
    Object.entries(currentThresholds).forEach(([component, threshold]: [string, any]) => {
      console.log(`  ${component}: ${(threshold * 100).toFixed(0)}%`);
    });
  }
  console.log();

  // Extract with strict thresholds
  console.log("=== Extraction with 0.90 Thresholds ===");
  const address = "House 12, Road 5, Mirpur, Dhaka-1216";
  const result = await extractor.extract(address);

  console.log("Input Address:", address);
  console.log("\nExtracted Components:");
  console.log(`  House Number: ${result.components.house_number || 'N/A (below threshold)'}`);
  console.log(`  Road: ${result.components.road || 'N/A (below threshold)'}`);
  console.log(`  Area: ${result.components.area || 'N/A (below threshold)'}`);
  console.log(`  District: ${result.components.district || 'N/A (below threshold)'}`);
  console.log(`  Division: ${result.components.division || 'N/A (below threshold)'}`);
  console.log(`  Postal Code: ${result.components.postal_code || 'N/A (below threshold)'}`);
  console.log(`  Flat Number: ${result.components.flat_number || 'N/A (below threshold)'}`);
  console.log(`  Floor Number: ${result.components.floor_number || 'N/A (below threshold)'}`);
  console.log(`  Block Number: ${result.components.block_number || 'N/A (below threshold)'}`);
  console.log(`\nOverall Confidence: ${(result.overall_confidence * 100).toFixed(1)}%`);
  console.log();

  // Example 2: Multiple addresses with strict thresholds
  console.log("=== Testing Multiple Addresses ===");
  const addresses = [
    "House 12, Road 5, Mirpur, Dhaka-1216",
    "Flat A-3, Building 7, Bashundhara R/A, Dhaka",
    "Banani, Dhaka-1213",
    "House 45, Road 8, Halishahar, Chittagong-4219",
  ];

  for (const addr of addresses) {
    const result = await extractor.extract(addr);
    const extractedCount = Object.values(result.components).filter(v => v).length;
    
    console.log(`\nAddress: ${addr}`);
    console.log(`  Components Extracted: ${extractedCount}/9`);
    console.log(`  Confidence: ${(result.overall_confidence * 100).toFixed(1)}%`);
    
    if (extractedCount === 0) {
      console.log(`  ⚠️  No components met the 0.90 threshold`);
    }
  }

  // Example 3: Compare with default thresholds
  console.log("\n=== Comparison: 0.90 vs Default Thresholds ===");
  const testAddress = "House 12, Road 5, Mirpur, Dhaka-1216";

  // Extract with strict thresholds (0.90)
  const strictResult = await extractor.extract(testAddress);
  const strictCount = Object.values(strictResult.components).filter(v => v).length;

  // Extract with default thresholds
  const defaultExtractor = new AddressExtractor();
  const defaultResult = await defaultExtractor.extract(testAddress);
  const defaultCount = Object.values(defaultResult.components).filter(v => v).length;

  console.log(`Address: ${testAddress}\n`);
  console.log("With 0.90 Thresholds:");
  console.log(`  Components: ${strictCount}/9`);
  console.log(`  Confidence: ${(strictResult.overall_confidence * 100).toFixed(1)}%`);
  console.log("\nWith Default Thresholds:");
  console.log(`  Components: ${defaultCount}/9`);
  console.log(`  Confidence: ${(defaultResult.overall_confidence * 100).toFixed(1)}%`);
  console.log(`\nDifference: ${defaultCount - strictCount} more components with default thresholds`);
}

main().catch(console.error);
