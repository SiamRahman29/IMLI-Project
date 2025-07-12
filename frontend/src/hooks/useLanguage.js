import { useState, useEffect } from 'react';

// Bengali translations for trending analysis page
const translations = {
  'ট্রেন্ডিং বিশ্লেষণ': 'Trending Analysis',
  'ট্রেন্ডিং ক্রেজ': 'Trending Craze',
  'দৈনিক সারসংক্ষেপ': 'Daily Summary', 
  'সাপ্তাহিক সারসংক্ষেপ': 'Weekly Summary',
  'পরিসংখ্যান': 'Statistics',
  'ফিল্টার অপশন': 'Filter Options',
  'ট্রেন্ডিং শব্দ খুঁজুন': 'Search Trending Words',
  'ফুল তারিখ নির্বাচন': 'Select Date Range',
  'ভর তারিখ': 'Start Date',
  'শেষ তারিখ': 'End Date', 
  'উৎস': 'Source',
  'ধরন': 'Category',
  'সীমা': 'Limit',
  'সর্ব তারিখ নির্বাচন': 'All Time',
  'গত ৭ দিন': 'Last 7 Days',
  'গত ৩০ দিন': 'Last 30 Days',
  'আজ': 'Today',
  'সব': 'All',
  'খুঁজুন': 'Search',
  'Enter': 'Enter',
  'শীর্ষ ট্রেন্ডিং ক্রেজ': 'Top Trending Phrases',
  'Export CSV': 'Export CSV',
  // Login page translations - always keep in English
  'Sign in to BARTA-IMLI': 'Sign in to BARTA-IMLI',
  'Please sign in to your account': 'Please sign in to your account',
  // UI elements that should always stay in English
  'ফিল্টার অপশন': 'Filter Options',
  'ট্রেন্ডিং শব্দ খুঁজুন': 'Search Trending Words'
};

export const useLanguage = () => {
  const [isBengali, setIsBengali] = useState(false);

  useEffect(() => {
    // Function to detect if page is translated to Bengali
    const detectBengaliTranslation = () => {
      // Check if Google Translate is active and set to Bengali
      const gtCombo = document.querySelector('.goog-te-combo');
      if (gtCombo && gtCombo.value === 'bn') {
        return true;
      }

      // Check for common Bengali text patterns in the DOM
      const bodyText = document.body.innerText || '';
      const bengaliPattern = /[\u0980-\u09FF]/;
      const bengaliWordCount = (bodyText.match(bengaliPattern) || []).length;
      
      // If more than 10% of text contains Bengali characters, consider it Bengali
      return bengaliWordCount > bodyText.length * 0.1;
    };

    // Check language periodically
    const checkLanguage = () => {
      const isCurrentlyBengali = detectBengaliTranslation();
      setIsBengali(isCurrentlyBengali);
    };

    // Initial check
    checkLanguage();

    // Set up observer for DOM changes (translation changes)
    const observer = new MutationObserver(checkLanguage);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });

    // Also check when window focus changes (in case user uses browser translate)
    window.addEventListener('focus', checkLanguage);

    return () => {
      observer.disconnect();
      window.removeEventListener('focus', checkLanguage);
    };
  }, []);

  const translate = (text) => {
    // For login page and certain UI elements, always return English
    if (translations[text]) {
      return translations[text];
    }
    // Otherwise return original text
    return text;
  };

  return { isBengali, translate };
};

export default useLanguage;
