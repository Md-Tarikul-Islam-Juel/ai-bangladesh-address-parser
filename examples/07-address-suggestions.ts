/**
 * Example 7: Address Autocomplete & Suggestions
 * 
 * This example demonstrates getting address suggestions
 * as users type, useful for autocomplete functionality.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  // Example 1: Search by area name
  console.log("=== Example 1: Search by Area Name ===");
  const suggestions1 = await extractor.suggest("Mirpur", 5);

  console.log(`Found ${suggestions1.length} suggestions for "Mirpur":\n`);
  suggestions1.forEach((suggestion, index) => {
    console.log(`${index + 1}. ${suggestion.area || suggestion.district || 'N/A'}`);
    if (suggestion.district) console.log(`   District: ${suggestion.district}`);
    if (suggestion.division) console.log(`   Division: ${suggestion.division}`);
    if (suggestion.postal_code) console.log(`   Postal Code: ${suggestion.postal_code}`);
    console.log(`   Confidence: ${(suggestion.confidence * 100).toFixed(1)}%`);
    console.log(`   Source: ${suggestion.source}`);
    console.log();
  });

  // Example 2: Search by district name
  console.log("=== Example 2: Search by District Name ===");
  const suggestions2 = await extractor.suggest("Dhak", 3);

  console.log(`Found ${suggestions2.length} suggestions for "Dhak":\n`);
  suggestions2.forEach((suggestion, index) => {
    console.log(`${index + 1}. ${suggestion.district || suggestion.area || 'N/A'}`);
    if (suggestion.division) console.log(`   Division: ${suggestion.division}`);
    console.log(`   Confidence: ${(suggestion.confidence * 100).toFixed(1)}%`);
    console.log();
  });

  // Example 3: Autocomplete simulation
  console.log("=== Example 3: Autocomplete Simulation ===");
  const userInputs = ["M", "Mi", "Mir", "Mirp", "Mirpur"];

  for (const input of userInputs) {
    const suggestions = await extractor.suggest(input, 3);
    console.log(`User typed: "${input}"`);
    console.log(`Suggestions: ${suggestions.map(s => s.area || s.district).join(", ")}`);
    console.log();
  }

  // Example 4: Using suggestions to complete address
  console.log("=== Example 4: Completing Incomplete Address ===");
  const incompleteAddress = "House 12, Road 5, Mirp";  // User typing "Mirpur"

  // Get suggestions for the incomplete area
  const suggestions3 = await extractor.suggest("Mirp", 1);
  
  if (suggestions3.length > 0) {
    const topSuggestion = suggestions3[0];
    console.log("Incomplete Address:", incompleteAddress);
    console.log("Top Suggestion:", topSuggestion.area || topSuggestion.district);
    console.log("Suggested Complete Address:");
    console.log(`  House 12, Road 5, ${topSuggestion.area || topSuggestion.district}, ${topSuggestion.district || ''}${topSuggestion.postal_code ? `-${topSuggestion.postal_code}` : ''}`);
  }

  // Example 5: Search for popular areas
  console.log("\n=== Example 5: Popular Areas Search ===");
  const popularAreas = ["Gulshan", "Banani", "Dhanmondi", "Uttara"];

  for (const area of popularAreas) {
    const suggestions = await extractor.suggest(area, 1);
    if (suggestions.length > 0) {
      const s = suggestions[0];
      console.log(`${area}:`);
      console.log(`  District: ${s.district || 'N/A'}`);
      console.log(`  Postal Code: ${s.postal_code || 'N/A'}`);
      console.log(`  Confidence: ${(s.confidence * 100).toFixed(1)}%`);
      console.log();
    }
  }
}

main().catch(console.error);
