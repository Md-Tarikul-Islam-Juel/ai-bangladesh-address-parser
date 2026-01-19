/**
 * Example 9: Address Enrichment
 * 
 * This example demonstrates enriching addresses with
 * additional geographic information and data.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  // Example 1: Basic enrichment
  console.log("=== Example 1: Basic Enrichment ===");
  const address1 = "Mirpur, Dhaka";
  const enriched1 = await extractor.enrich(address1);

  console.log("Original Address:", address1);
  console.log("\nEnriched Data:");
  console.log("Components:", JSON.stringify(enriched1.components, null, 2));
  
  if (enriched1.hierarchy) {
    console.log("Hierarchy:", enriched1.hierarchy);
  }
  
  if (enriched1.suggested_postal_code) {
    console.log("Suggested Postal Code:", enriched1.suggested_postal_code);
  }
  
  console.log("Overall Confidence:", `${(enriched1.overall_confidence * 100).toFixed(1)}%`);
  console.log();

  // Example 2: Enrichment for incomplete address
  console.log("=== Example 2: Enriching Incomplete Address ===");
  const address2 = "House 12, Road 5, Mirpur";
  const enriched2 = await extractor.enrich(address2);

  console.log("Original Address:", address2);
  console.log("\nEnriched Components:");
  Object.entries(enriched2.components).forEach(([key, value]) => {
    if (value) {
      console.log(`  ${key}: ${value}`);
    }
  });

  if (enriched2.suggested_postal_code) {
    console.log("\nSuggested Postal Code:", enriched2.suggested_postal_code);
  }
  console.log();

  // Example 3: Enrichment for delivery management
  console.log("=== Example 3: Delivery Management Enrichment ===");
  const deliveryAddresses = [
    "House 12, Mirpur, Dhaka",
    "Banani, Dhaka",
    "Gulshan 2, Dhaka",
  ];

  interface DeliveryInfo {
    address: string;
    components: any;
    postal_code?: string;
    confidence: number;
  }

  const deliveryInfo: DeliveryInfo[] = [];

  for (const address of deliveryAddresses) {
    const enriched = await extractor.enrich(address);
    deliveryInfo.push({
      address,
      components: enriched.components,
      postal_code: enriched.components.postal_code || enriched.suggested_postal_code,
      confidence: enriched.overall_confidence,
    });
  }

  console.log("Delivery Information:");
  deliveryInfo.forEach((info, index) => {
    console.log(`\n${index + 1}. ${info.address}`);
    console.log(`   Area: ${info.components.area || 'N/A'}`);
    console.log(`   District: ${info.components.district || 'N/A'}`);
    console.log(`   Postal Code: ${info.postal_code || 'N/A'}`);
    console.log(`   Confidence: ${(info.confidence * 100).toFixed(1)}%`);
  });

  // Example 4: Enrichment for data analytics
  console.log("\n=== Example 4: Analytics Enrichment ===");
  const address4 = "House 45, Road 8, Halishahar, Chittagong";
  const enriched4 = await extractor.enrich(address4);

  console.log("Address:", address4);
  console.log("\nAnalytics Data:");
  console.log("  Division:", enriched4.components.division || 'N/A');
  console.log("  District:", enriched4.components.district || 'N/A');
  console.log("  Area:", enriched4.components.area || 'N/A');
  console.log("  Postal Code:", enriched4.components.postal_code || enriched4.suggested_postal_code || 'N/A');
  
  console.log("  Data Quality Score:", `${(enriched4.overall_confidence * 100).toFixed(1)}%`);

  // Example 5: Complete enrichment output
  console.log("\n=== Example 5: Complete Enrichment Output ===");
  const address5 = "House 12, Road 5, Mirpur, Dhaka-1216";
  const enriched5 = await extractor.enrich(address5);

  console.log("Complete Enrichment Data (JSON):");
  console.log(JSON.stringify(enriched5, null, 2));
}

main().catch(console.error);
