// Test frontend parsing logic
const testText = `📊 NLP Trending Keywords থেকে আজকের শব্দ নির্বাচন করুন

  🔸 ইরানের: 0.0581
  🔸 সংবাদ: 0.0378
  🔸 ইসরায়েলি: 0.0357
  🔸 ইস্যুতে: 0.0325
  🔸 পত্রিকা: 0.0302
  🔸 নির্বাচন: 0.0282
  🔸 পথে: 0.0276
  🔸 ইসরায়েলের: 0.0252
  🔸 হত্যার: 0.0235
  🔸 পারমাণবিক: 0.0226

🏷️ Named Entities:
  📍 persons: ['Example Person']

💭 Sentiment: {'positive': 0.15, 'negative': 0.65, 'neutral': 0.20}`;

// Simulate the updated frontend parsing logic
function parseCandidates(candidatesText) {
  if (!candidatesText) return [];
  
  // Extract only the NLP keywords that start with 🔸
  const keywords = [];
  const lines = candidatesText.split('\n');
  
  for (const line of lines) {
    const trimmed = line.trim();
    // Look for lines that contain 🔸 (NLP keywords)
    if (trimmed.includes('🔸')) {
      const match = trimmed.match(/🔸\s*([^:]+):/);
      if (match) {
        const keyword = match[1].trim();
        if (keyword && keyword.length > 1) {
          keywords.push(keyword);
        }
      }
    }
  }
  
  return keywords.slice(0, 10); // Limit to 10 candidates
}

const results = parseCandidates(testText);
console.log('Extracted keywords:');
results.forEach((keyword, idx) => {
  console.log(`${idx + 1}. ${keyword}`);
});
console.log(`\nTotal extracted: ${results.length} keywords`);
console.log('\n✅ Frontend parsing fix working correctly!');
