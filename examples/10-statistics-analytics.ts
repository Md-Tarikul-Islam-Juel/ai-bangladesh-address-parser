/**
 * Example 10: Statistics & Analytics
 * 
 * This example demonstrates calculating statistics
 * for multiple addresses for data analysis.
 */

import { AddressExtractor } from "../dist/index";

async function main() {
  const extractor = new AddressExtractor();

  // Example 1: Basic statistics
  console.log("=== Example 1: Basic Statistics ===");
  const addresses1 = [
    "House 12, Mirpur, Dhaka",
    "Banani, Dhaka",
    "Gulshan 2, Dhaka",
    "Dhanmondi, Dhaka",
    "House 45, Road 8, Halishahar, Chittagong",
  ];

  const stats1 = await extractor.getStatistics(addresses1);

  console.log("Statistics Summary:");
  console.log(`  Total Addresses: ${stats1.total}`);
  console.log(`  Average Completeness: ${(stats1.completeness * 100).toFixed(1)}%`);
  console.log(`  Average Confidence: ${(stats1.average_confidence * 100).toFixed(1)}%`);
  console.log();

  // Example 2: Geographic distribution
  console.log("=== Example 2: Geographic Distribution ===");
  const addresses2 = [
    "House 12, Mirpur, Dhaka",
    "Banani, Dhaka",
    "Gulshan, Dhaka",
    "Dhanmondi, Dhaka",
    "House 45, Chittagong",
    "Agrabad, Chittagong",
    "Sylhet",
  ];

  const stats2 = await extractor.getStatistics(addresses2);

  console.log("District Distribution:");
  Object.entries(stats2.distribution.districts).forEach(([district, count]: [string, any]) => {
    console.log(`  ${district}: ${count}`);
  });
  console.log();

  console.log("Division Distribution:");
  Object.entries(stats2.distribution.divisions).forEach(([division, count]: [string, any]) => {
    console.log(`  ${division}: ${count}`);
  });
  console.log();

  console.log("Top Areas:");
  stats2.common_areas.forEach((area: any, index: number) => {
    console.log(`  ${index + 1}. ${area.area}: ${area.count} occurrence(s)`);
  });
  console.log();

  // Example 3: Data quality analysis
  console.log("=== Example 3: Data Quality Analysis ===");
  const addresses3 = [
    "House 12, Road 5, Mirpur, Dhaka-1216",  // Complete
    "Banani, Dhaka",                          // Missing postal
    "House 45, Chittagong",                   // Missing area and postal
    "Gulshan 2, Dhaka-1212",                  // Complete
  ];

  const stats3 = await extractor.getStatistics(addresses3);

  console.log("Data Quality Metrics:");
  console.log(`  Completeness: ${(stats3.completeness * 100).toFixed(1)}%`);
  console.log(`  Average Confidence: ${(stats3.average_confidence * 100).toFixed(1)}%`);
  console.log();

  console.log("Missing Components:");
  Object.entries(stats3.missing_components).forEach(([component, count]: [string, any]) => {
    const percentage = (count / stats3.total) * 100;
    console.log(`  ${component}: ${count} (${percentage.toFixed(1)}%)`);
  });
  console.log();

  // Example 4: Business intelligence
  console.log("=== Example 4: Business Intelligence ===");
  const customerAddresses = [
    "House 12, Mirpur, Dhaka",
    "Banani, Dhaka",
    "Gulshan, Dhaka",
    "Dhanmondi, Dhaka",
    "House 45, Chittagong",
    "Agrabad, Chittagong",
    "Sylhet",
    "Rajshahi",
  ];

  const stats4 = await extractor.getStatistics(customerAddresses);

  console.log("Customer Distribution Analysis:");
  console.log(`  Total Customers: ${stats4.total}`);
  console.log();

  console.log("By District:");
  const districtEntries = Object.entries(stats4.distribution.districts)
    .sort(([, a]: [string, any], [, b]: [string, any]) => b - a);
  
  districtEntries.forEach(([district, count]: [string, any]) => {
    const percentage = (count / stats4.total) * 100;
    console.log(`  ${district}: ${count} (${percentage.toFixed(1)}%)`);
  });
  console.log();

  console.log("By Division:");
  const divisionEntries = Object.entries(stats4.distribution.divisions)
    .sort(([, a]: [string, any], [, b]: [string, any]) => b - a);
  
  divisionEntries.forEach(([division, count]: [string, any]) => {
    const percentage = (count / stats4.total) * 100;
    console.log(`  ${division}: ${count} (${percentage.toFixed(1)}%)`);
  });
  console.log();

  // Example 5: Complete statistics report
  console.log("=== Example 5: Complete Statistics Report ===");
  const addresses5 = [
    "House 12, Road 5, Mirpur, Dhaka-1216",
    "Flat A-3, Bashundhara R/A, Dhaka",
    "Banani, Dhaka-1213",
    "Gulshan 2, Dhaka-1212",
    "House 45, Road 8, Halishahar, Chittagong-4219",
  ];

  const stats5 = await extractor.getStatistics(addresses5);

  console.log("Complete Statistics Report:");
  console.log(JSON.stringify(stats5, null, 2));
}

main().catch(console.error);
