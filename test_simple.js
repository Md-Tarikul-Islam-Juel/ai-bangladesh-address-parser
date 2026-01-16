// Simple test script
const { AddressExtractor } = require('./dist/index');

async function test() {
  console.log('🧪 Testing Address Extractor...\n');
  
  const extractor = new AddressExtractor();
  
  try {
    const result = await extractor.extract('House 12, Road 5, Mirpur, Dhaka-1216');
    
    console.log('✅ Success!');
    console.log('Components:', result.components);
    console.log('Confidence:', result.overall_confidence);
    console.log('Time:', result.extraction_time_ms, 'ms');
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  }
}

test();
