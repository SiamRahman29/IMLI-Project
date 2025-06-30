#!/usr/bin/env python3
"""
Quick validation test for the fixed routes
"""
import sys
import os
sys.path.append('.')

def test_route_validation():
    print("🧪 Testing route validation after fixes...")
    
    try:
        # Test imports
        from app.routes.routes_new import router
        print("✅ Routes module imported successfully")
        
        # Test FastAPI router functionality
        routes = router.routes
        print(f"✅ Router has {len(routes)} routes registered")
        
        # List all available routes
        print("\n📋 Available routes:")
        for route in routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if hasattr(route.methods, '__iter__') else [route.methods]
                print(f"  {' '.join(methods)} {route.path}")
        
        # Test specific imports that were causing issues
        try:
            from groq import Groq
            print("✅ Groq import successful")
        except Exception as e:
            print(f"❌ Groq import failed: {e}")
            
        try:
            from app.services.category_llm_analyzer import get_জাতীয়_trending_words
            print("✅ Category LLM analyzer import successful")
        except Exception as e:
            print(f"❌ Category LLM analyzer import failed: {e}")
        
        try:
            from enhanced_reddit_category_scraper import EnhancedRedditCategoryScraper
            print("✅ Enhanced Reddit scraper import successful")
        except Exception as e:
            print(f"❌ Enhanced Reddit scraper import failed: {e}")
        
        print("\n🎉 All validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Route validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_route_validation()
    if success:
        print("\n✅ Your routes are ready to use!")
        print("🚀 You can now start your FastAPI server:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("\n❌ Please fix the errors above before starting the server.")
        sys.exit(1)
