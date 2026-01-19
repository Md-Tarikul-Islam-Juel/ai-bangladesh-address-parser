/**
 * Example 6: Address Comparison & Similarity
 * 
 * This example demonstrates comparing two addresses
 * to detect duplicates and calculate similarity scores.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  // Example 1: Similar addresses (likely duplicates)
  console.log("=== Example 1: Similar Addresses ===");
  const addr1 = "House 12, Road 5, Mirpur, Dhaka-1216";
  const addr2 = "H-12, R-5, Mirpur, Dhaka";

  const comparison1 = await extractor.compare(addr1, addr2);

  console.log("Address 1:", addr1);
  console.log("Address 2:", addr2);
  console.log("Similarity:", `${(comparison1.similarity * 100).toFixed(1)}%`);
  console.log("Weighted Score:", comparison1.score.toFixed(3));
  console.log("Match:", comparison1.match ? "✅ Yes" : "❌ No");
  console.log("Common Components:", comparison1.common.join(", "));
  console.log("Different Components:", comparison1.differences.join(", ") || "None");
  console.log();

  // Example 2: Identical addresses
  console.log("=== Example 2: Identical Addresses ===");
  const addr3 = "House 12, Road 5, Mirpur, Dhaka-1216";
  const addr4 = "House 12, Road 5, Mirpur, Dhaka-1216";

  const comparison2 = await extractor.compare(addr3, addr4);

  console.log("Address 1:", addr3);
  console.log("Address 2:", addr4);
  console.log("Similarity:", `${(comparison2.similarity * 100).toFixed(1)}%`);
  console.log("Match:", comparison2.match ? "✅ Yes" : "❌ No");
  console.log();

  // Example 3: Different addresses
  console.log("=== Example 3: Different Addresses ===");
  const addr5 = "House 12, Road 5, Mirpur, Dhaka-1216";
  const addr6 = "Banani, Dhaka-1213";

  const comparison3 = await extractor.compare(addr5, addr6);

  console.log("Address 1:", addr5);
  console.log("Address 2:", addr6);
  console.log("Similarity:", `${(comparison3.similarity * 100).toFixed(1)}%`);
  console.log("Match:", comparison3.match ? "✅ Yes" : "❌ No");
  console.log("Common Components:", comparison3.common.join(", ") || "None");
  console.log();

  // Example 4: Duplicate detection in a list
  console.log("=== Example 4: Duplicate Detection ===");
  const addresses = [
    "House 12, Road 5, Mirpur, Dhaka-1216",
    "H-12, R-5, Mirpur, Dhaka",
    "House 12, Road 5, Mirpur, Dhaka-1216",  // Duplicate
    "Banani, Dhaka-1213",
    "House 12, Road 5, Mirpur, Dhaka",        // Similar to first
  ];

  console.log("Checking for duplicates...\n");
  const duplicates: Array<{ index1: number; index2: number; similarity: number }> = [];

  for (let i = 0; i < addresses.length; i++) {
    for (let j = i + 1; j < addresses.length; j++) {
      const comparison = await extractor.compare(addresses[i], addresses[j]);
      if (comparison.match) {
        duplicates.push({
          index1: i,
          index2: j,
          similarity: comparison.similarity,
        });
      }
    }
  }

  if (duplicates.length > 0) {
    console.log("Duplicates Found:");
    duplicates.forEach((dup) => {
      console.log(`  ${dup.index1 + 1}. "${addresses[dup.index1]}"`);
      console.log(`  ${dup.index2 + 1}. "${addresses[dup.index2]}"`);
      console.log(`     Similarity: ${(dup.similarity * 100).toFixed(1)}%\n`);
    });
  } else {
    console.log("No duplicates found.");
  }

  // Example 5: Component-level comparison
  console.log("=== Example 5: Component-Level Comparison ===");
  const comparison4 = await extractor.compare(addr1, addr2);
  
  if (comparison4.component_similarities) {
    console.log("Component Similarities:");
    Object.entries(comparison4.component_similarities).forEach(([component, similarity]: [string, any]) => {
      console.log(`  ${component}: ${(similarity * 100).toFixed(1)}%`);
    });
  }
}

main().catch(console.error);
