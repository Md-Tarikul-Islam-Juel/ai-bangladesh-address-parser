/**
 * Example 2: Detailed Address Extraction
 * 
 * This example demonstrates extraction with detailed metadata
 * showing confidence scores and extraction sources.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  const address = "House 12, Road 5, Mirpur, Dhaka-1216";

  // Extract with detailed metadata
  const result = await extractor.extract(address, { detailed: true });

  console.log("=== Detailed Extraction Results ===");
  console.log("Original Address:", result.original_address);
  console.log("Normalized Address:", result.normalized_address);
  console.log("Overall Confidence:", `${(result.overall_confidence * 100).toFixed(1)}%`);
  console.log("Extraction Time:", `${result.extraction_time_ms.toFixed(2)}ms`);
  console.log();

  if (result.metadata) {
    console.log("=== Metadata ===");
    console.log("Script:", result.metadata.script);
    console.log("Is Mixed Script:", result.metadata.is_mixed);
    console.log("Enabled Stages:", result.metadata.enabled_stages?.join(", "));
    console.log();

    if (result.metadata.component_details) {
      console.log("=== Component Details ===");
      Object.entries(result.metadata.component_details).forEach(([component, details]: [string, any]) => {
        console.log(`${component}:`);
        console.log(`  Value: ${details.value}`);
        console.log(`  Confidence: ${(details.confidence * 100).toFixed(1)}%`);
        console.log(`  Source: ${details.source}`);
        console.log();
      });
    }

    if (result.metadata.conflicts && result.metadata.conflicts.length > 0) {
      console.log("=== Conflicts Detected ===");
      result.metadata.conflicts.forEach((conflict: string) => {
        console.log(`  - ${conflict}`);
      });
      console.log();
    }
  }

  console.log("=== Extracted Components ===");
  Object.entries(result.components).forEach(([key, value]) => {
    if (value) {
      console.log(`${key}: ${value}`);
    }
  });
}

main().catch(console.error);
