/**
 * Example 3: Batch Address Extraction
 * 
 * This example demonstrates processing multiple addresses
 * with progress tracking and error handling.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  const addresses = [
    "House 12, Road 5, Mirpur, Dhaka",
    "Flat A-3, Building 7, Bashundhara R/A, Dhaka",
    "Banani, Dhaka",
    "Gulshan 2, Dhaka",
    "Dhanmondi 15, Dhaka",
    "House 45, Road 8, Halishahar, Chittagong-4219",
  ];

  console.log("=== Batch Extraction ===");
  console.log(`Processing ${addresses.length} addresses...\n`);

  // Batch extraction with progress tracking
  const results = await extractor.batchExtract(addresses, {
    onProgress: (current, total) => {
      const percentage = ((current / total) * 100).toFixed(1);
      console.log(`Progress: ${current}/${total} (${percentage}%)`);
    },
    onError: (address, error) => {
      console.error(`Error processing "${address}":`, error.message);
    },
  });

  console.log("\n=== Results ===");
  results.forEach((result, index) => {
    const addr = addresses[index];
    const comp = result.components;

    console.log(`\n${index + 1}. ${addr}`);
    console.log(`   Confidence: ${(result.overall_confidence * 100).toFixed(1)}%`);
    
    if (comp.house_number) console.log(`   House: ${comp.house_number}`);
    if (comp.road) console.log(`   Road: ${comp.road}`);
    if (comp.area) console.log(`   Area: ${comp.area}`);
    if (comp.district) console.log(`   District: ${comp.district}`);
    if (comp.postal_code) console.log(`   Postal Code: ${comp.postal_code}`);
    
    if (Object.values(comp).every(v => !v)) {
      console.log("   ⚠️  No components extracted");
    }
  });

  // Summary statistics
  const successful = results.filter(r => r.overall_confidence > 0).length;
  const avgConfidence = results.reduce((sum, r) => sum + r.overall_confidence, 0) / results.length;

  console.log("\n=== Summary ===");
  console.log(`Total: ${results.length}`);
  console.log(`Successful: ${successful}`);
  console.log(`Average Confidence: ${(avgConfidence * 100).toFixed(1)}%`);
}

main().catch(console.error);
