#!/usr/bin/env python3
"""
Unit tests for TikTok scraper utility functions.
Can be run with pytest or as a standalone script.
"""

import sys
from base import convert_to_numeric, calculate_engagement_score, analyze_sentiment


def test_convert_to_numeric():
    """Test convert_to_numeric function with various inputs"""
    # K suffix tests
    assert convert_to_numeric('1.5K') == 1500, 'Failed: 1.5K conversion'
    assert convert_to_numeric('2.3K') == 2300, 'Failed: 2.3K conversion'
    assert convert_to_numeric('100K') == 100000, 'Failed: 100K conversion'
    
    # M suffix tests
    assert convert_to_numeric('2.3M') == 2300000, 'Failed: 2.3M conversion'
    assert convert_to_numeric('1.5M') == 1500000, 'Failed: 1.5M conversion'
    assert convert_to_numeric('10M') == 10000000, 'Failed: 10M conversion'
    
    # B suffix tests
    assert convert_to_numeric('1B') == 1000000000, 'Failed: 1B conversion'
    assert convert_to_numeric('2.5B') == 2500000000, 'Failed: 2.5B conversion'
    
    # Edge cases
    assert convert_to_numeric('N/A') is None, 'Failed: N/A should return None'
    assert convert_to_numeric('') is None, 'Failed: empty string should return None'
    assert convert_to_numeric(None) is None, 'Failed: None should return None'
    
    print('[PASS] convert_to_numeric tests passed')


def test_calculate_engagement_score():
    """Test calculate_engagement_score function"""
    # Test with valid inputs
    score = calculate_engagement_score('#test', '100K', 'Music', 'test')
    assert 1.0 <= score <= 10.0, f'Failed: score {score} out of range (1-10)'
    
    # Test with high engagement category
    score_high = calculate_engagement_score('#viral', '5M', 'Entertainment', 'viral content')
    assert 1.0 <= score_high <= 10.0, f'Failed: score {score_high} out of range'
    
    # Test with low engagement
    score_low = calculate_engagement_score('#test', '100', 'General', 'test')
    assert 1.0 <= score_low <= 10.0, f'Failed: score {score_low} out of range'
    
    print('[PASS] calculate_engagement_score tests passed')


def test_analyze_sentiment():
    """Test analyze_sentiment function"""
    # Test sentiment analysis
    polarity, label = analyze_sentiment('#test', 'test text')
    assert isinstance(polarity, float), 'Failed: polarity should be float'
    assert isinstance(label, str), 'Failed: label should be string'
    assert label == 'Neutral', 'Failed: sentiment should be neutral (placeholder)'
    assert polarity == 0.0, 'Failed: polarity should be 0.0 (placeholder)'
    
    # Test with different inputs
    polarity2, label2 = analyze_sentiment('#viral', 'viral content')
    assert isinstance(polarity2, float), 'Failed: polarity2 should be float'
    assert isinstance(label2, str), 'Failed: label2 should be string'
    
    print('[PASS] analyze_sentiment tests passed')


def run_all_tests():
    """Run all tests and return success status"""
    try:
        test_convert_to_numeric()
        test_calculate_engagement_score()
        test_analyze_sentiment()
        print('\n' + '='*50)
        print('[PASS] All tests passed successfully!')
        print('='*50)
        return True
    except AssertionError as e:
        print(f'\n[FAIL] Test failed: {e}')
        return False
    except Exception as e:
        print(f'\n[ERROR] Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Run as standalone script
    success = run_all_tests()
    sys.exit(0 if success else 1)

