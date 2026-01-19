/**
 * Test script for address extraction
 */

import { AddressExtractor } from './index';

async function test() {
  console.log('🧪 Testing Bangladesh Address Extractor\n');
  
  const extractor = new AddressExtractor();
  
  // Test addresses
  const testAddresses = [
    'House 12, Road 5, Mirpur, Dhaka-1216',
    'Flat A-3, Building 7, Bashundhara R/A, Dhaka',
    'Banani, Dhaka',
    '1152/C "Greenhouse", House# 45, Road# 08, Shapla Residential Area, Halishahar, Chittagong-4219',
  ];
  
  console.log(`Testing ${testAddresses.length} addresses...\n`);
  
  for (const address of testAddresses) {
    console.log(`📋 Address: ${address}`);
    
    try {
      const result = await extractor.extract(address);
      
      console.log(`  ✅ Confidence: ${(result.overall_confidence * 100).toFixed(1)}%`);
      console.log(`  ⏱️  Time: ${result.extraction_time_ms.toFixed(2)}ms`);
      console.log(`  📦 Components:`);
      
      if (result.components.house_number) {
        console.log(`     - House: ${result.components.house_number}`);
      }
      if (result.components.road) {
        console.log(`     - Road: ${result.components.road}`);
      }
      if (result.components.area) {
        console.log(`     - Area: ${result.components.area}`);
      }
      if (result.components.district) {
        console.log(`     - District: ${result.components.district}`);
      }
      if (result.components.postal_code) {
        console.log(`     - Postal Code: ${result.components.postal_code}`);
      }
      
      console.log('');
    } catch (error) {
      console.error(`  ❌ Error: ${error instanceof Error ? error.message : String(error)}`);
      console.log('');
    }
  }
  
  console.log('✅ Tests complete!');
}

test().catch(console.error);
