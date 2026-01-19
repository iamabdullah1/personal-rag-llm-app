"""
Test script to verify semantic cache is working correctly
"""
from app.services.semantic_cache import semantic_cache

print('=' * 60)
print('SEMANTIC CACHE TEST')
print('=' * 60)

# Clear any existing cache first
semantic_cache.clear()

# Test 1: Add a Q&A pair
print('\n📝 Test 1: Adding Q&A to cache...')
semantic_cache.add('What are your skills?', 'I specialize in Python, React, and AI/ML development.')
stats = semantic_cache.get_stats()
print(f'   Cache entries: {stats["total_entries"]}')

# Test 2: Exact match (same question)
print('\n🔍 Test 2: Exact match - same question...')
result = semantic_cache.get_exact_match('What are your skills?')
if result:
    print(f'   ✅ MATCH: {result[:50]}...')
else:
    print('   ❌ No match (unexpected!)')

# Test 3: Exact match (slightly different phrasing - should match ~85%+)
print('\n🔍 Test 3: Similar question (should match above 85%)...')
result = semantic_cache.get_exact_match('What skills do you have?')
if result:
    print(f'   ✅ MATCH: {result[:50]}...')
else:
    print('   ❌ No match - similarity below threshold')

# Test 4: Find similar (below 85% threshold)
print('\n🔍 Test 4: Finding similar cached Q&As (60-84% range)...')
similar = semantic_cache.find_similar('Tell me about your technical abilities')
print(f'   Found {len(similar)} similar Q&As')
for s in similar:
    print(f'   - "{s["question"][:40]}..." (similarity: {s["similarity"]:.1%})')

# Test 5: Unrelated question (should not match)
print('\n🔍 Test 5: Unrelated question (should NOT match)...')
result = semantic_cache.get_exact_match('What is the weather today?')
if result:
    print(f'   ❌ Unexpected match: {result[:50]}...')
else:
    print('   ✅ No match (correct behavior)')

print('\n' + '=' * 60)
print('Cache tests complete!')
print(f'Final stats: {semantic_cache.get_stats()}')
