STOP_WORDS = set([
    'এবং', 'বা', 'কিন্তু', 'তবে', 'যদি', 'তাহলে', 'কেননা', 'যেহেতু', 'অতএব', 'সুতরাং',
    'এর', 'তার', 'তাদের', 'আমার', 'আমাদের', 'তোমার', 'তোমাদের', 'তিনি', 'তারা', 'আমি', 'আমরা',
    'তুমি', 'তোমরা', 'সে', 'এই', 'এটি', 'ওই', 'ওটি', 'যে', 'যেটি', 'কী', 'কি', 'কেন', 'কোথায়',
    'কখন', 'কীভাবে', 'কোন', 'কত', 'কতটা', 'হয়', 'হয়েছে', 'হবে', 'হচ্ছে', 'থাকা', 'থাকে', 'থাকবে',
    'আছে', 'ছিল', 'থেকে', 'পর্যন্ত', 'দিয়ে', 'করে', 'জন্য', 'সাথে', 'মধ্যে', 'ভিতরে', 'বাইরে',
    'উপর', 'নিচে', 'আগে', 'পরে', 'সময়', 'দিন', 'রাত', 'সকাল', 'বিকাল', 'সন্ধ্যা', 'এখন', 'তখন',
    'একটি', 'একটা', 'দুটি', 'দুটো', 'তিনটি', 'তিনটে', 'চারটি', 'চারটে', 'পাঁচটি', 'পাঁচটে',
    'না', 'নেই', 'নয়', 'নি', 'অন্য', 'আরও', 'আরো', 'অনেক', 'সব', 'সকল', 'প্রতি', 'খুব', 'বেশ',
    'ভাল', 'ভালো', 'মন্দ', 'ভাল', 'মানুষ', 'লোক', 'জন', 'গুলি', 'গুলো', 'টি', 'টা', 'খানা', 'খানি',
    'টুকু', 'মত', 'মতো', 'মতন', 'হিসেবে','আরও পড়ুন', 'হিসেবে', 'রূপে', 'হিসেবে', 'বলে', 'বলা', 'বলেন', 'বলেছেন',
    'বলছেন', 'বলবেন', 'বর', 'বরং','দেশ', 'মাঝে', 'মাঝেমাঝে', 'কখনো', 'কখনও', 'সর্বদা', 'সবসময়', 'প্রায়',
    'প্রায়ই', 'কখনো', 'কদাচিৎ', 'মোটেও','শুক্রবার', 'মোটেই', 'একেবারে', 'একদম', 'পুরোপুরি', 'সম্পূর্ণ', 'সম্পূর্ণভাবে',
    'হয়তো', 'হয়ত', 'অবশ্যই', 'অবশ্য', 'নিশ্চয়', 'নিশ্চিত', 'সম্ভবত', 'হয়নি', 'নয়', 'না', 'কোনো',
    'কোন', 'কেউ', 'কেউই', 'কিছু', 'কিছুই', 'কোথাও', 'কোথাওই', 'কখনো', 'কখনোই', 'যখন', 'তখনই',
    'যেখানে', 'সেখানে', 'যেভাবে', 'সেভাবে', 'যতটা', 'ততটা', 'যতক্ষণ', 'ততক্ষণ', 'প্রথম', 'দ্বিতীয়',
    'তৃতীয়', 'চতুর্থ', 'পঞ্চম', 'ষষ্ঠ', 'সপ্তম', 'অষ্টম', 'নবম', 'দশম', 'একে', 'তাকে', 'তাদেরকে','তাদের',
    'আমাকে', 'আমাদেরকে', 'তোমাকে', 'তোমাদেরকে', 'এটাকে', 'ওটাকে', 'যাকে', 'কাকে', 'ঐ', 'ওই',
    'এই', 'সেই', 'যে','টিভিতে', 'আজকের', 'খেলা', 'টিভিতে আজকের খেলা', 'যেই', 'কোন', 'কোনো', 'একজন', 'দুজন', 'তিনজন', 'চারজন', 'পাঁচজন',
    'নতুন', 'পুরাতন', 'পুরোনো', 'বড়', 'ছোট', 'ভালো', 'খারাপ', 'সুন্দর', 'কুৎসিত', 'উচ্চ', 'নিম্ন',
    'অই', 'অগত্যা','বাংলাদেশ', 'টাকা','শতাংশ','পানি', 'অত: পর', 'অতএব', 'অথচ', 'অথবা', 'অধিক', 'অধীনে', 'অধ্যায়', 'অনুগ্রহ',
    'অনুভূত', 'অনুযায়ী','ঋণ', 'অনুরূপ', 'অনুসন্ধান', 'অনুসরণ', 'অনুসারে', 'অনুসৃত', 'অনেক', 'অনেকে',
    'অনেকেই', 'অন্তত', 'অন্য', 'অন্যত্র', 'অন্যান্য', 'অপেক্ষাকৃতভাবে', 'অবধি', 'অবশ্য', 'অবশ্যই',
    'অবস্থা','জাতীয়','সারাদেশ','অবিলম্বে', 'অভ্যন্তরস্থ', 'অর্জিত', 'অর্থাত', 'অসদৃশ', 'অসম্ভাব্য', 'আইন', 'আউট',
    'আক্রান্ত', 'আগামী', 'আগে', 'আগেই', 'আগ্রহী', 'আছে', 'আজ', 'আট', 'আদেশ', 'আদ্যভাগে', 'আন্দাজ',
    'আপনার', 'আপনি', 'আবার', 'আমরা', 'আমাকে', 'আমাদিগের', 'আমাদের', 'আমার', 'আমি', 'আর', 'আরও',
    'আশি', 'আশু', 'আসা', 'আসে', 'ই','বিএনপি', 'ইচ্ছা', 'ইচ্ছাপূর্বক', 'ইতিমধ্যে', 'ইতোমধ্যে', 'ইত্যাদি',
    'ইশারা', 'ইহা', 'ইহাতে', 'উক্তি', 'উচিত', 'উচ্চ', 'উঠা', 'উত্তম', 'উত্তর', 'উনি', 'উপর',
    'উপরে', 'উপলব্ধ', 'উপায়', 'উভয়', 'উল্লেখ', 'উল্লেখযোগ্যভাবে', 'উহার', 'ঊর্ধ্বতন', 'এ', 'এপর্যন্ত',
    'এঁদের', 'এঁরা', 'এই', 'এইগুলো', 'এইভাবে', 'এক', 'একই', 'একটি', 'একদা', 'একবার', 'একভাবে',
    'একরকম', 'একসঙ্গে', 'একা', 'একে', 'এক্', 'এখন', 'এখনও', 'এখনো', 'এখানে', 'এখানেই', 'এছাড়াও',
    'এটা', 'এটাই', 'এটি', 'এত', 'এতটাই', 'এতদ্বারা', 'এতে', 'এদিকে','ছবি','ট্রাম্প','পুলিশ','বিদেশ','রিপোর্টার','এদের', 'এপর্যন্ত', 'এবং',
    'এবার', 'এমন', 'এমনকি', 'এমনকী', 'এমনি', 'এর','অনলাইন ডেস্ক','ডেস্ক','অনলাইন', 'এরকম', 'এরা', 'এল', 'এলাকায়', 'এলাকার', 'এস',
    'এসে', 'ঐ', 'ও', 'ওঁদের', 'ওঁর', 'ওঁরা', 'ওই', 'ওকে', 'ওখানে', 'ওদের', 'ওর', 'ওরা', 'ওহে',
    'কক্ষ', 'কখন', 'কখনও', 'কত', 'কবে', 'কম', 'কমনে', 'কয়েক', 'কয়েকটি', 'করছে', 'করছেন', 'করতে',
    'করবে', 'করবেন', 'করলে', 'করলেন', 'করলো', 'করা', 'করাই', 'করাত', 'করার', 'করায়', 'করি',
    'করিতে', 'করিয়া', 'করিয়ে', 'করে', 'করেই', 'করেছিল', 'করেছিলেন', 'করেছে', 'করেছেন', 'করেন',
    'কর্তব্য', 'কাউকে', 'কাছ', 'কাছাকাছি', 'কাছে', 'কাজ', 'কাজে', 'কারও', 'কারণ', 'কারণসমূহ', 'কারো',
    'কি', 'কিংবা', 'কিছু', 'কিছুই', 'কিছুটা', 'কিছুনা', 'কিনা', 'কিন্তু', 'কিভাবে', 'কী', 'কূপ', 'কে',
    'কেউ', 'কেউই', 'কেউনা', 'কেখা', 'কেন', 'কেবল', 'কেবা', 'কেস', 'কেহ', 'কোটি', 'কোথা', 'কোথাও',
    'কোথায়', 'কোন', 'কোনও', 'কোনো', 'ক্রম', 'ক্ষেত্রে', 'কয়েক', 'কয়েকটি', 'খুঁজছেন', 'খুব',
    'খোলা', 'খোলে', 'গড়', 'গত', 'গিয়ে', 'গিয়েছিলাম', 'গিয়েছে', 'গিয়ে', 'গিয়েছে', 'গুরুত্ব', 'গুলি',
    'গেছে', 'গেল', 'গেলে', 'গোটা', 'গোষ্ঠীবদ্ধ', 'গ্রহণ', 'গ্রুপ', 'ঘর', 'ঘোষণা', 'চলে', 'চান', 'চায়',
    'চার', 'চালা', 'চালান', 'চালু', 'চায়', 'চেয়ে', 'চেয়েছিলেন', 'চেষ্টা', 'চেয়ে', 'ছয়', 'ছাড়া',
    'ছাড়াছাড়ি', 'ছাড়া', 'ছাড়াও', 'ছিল', 'ছিলেন', 'ছোট', 'জন', 'জনকে', 'জনাব', 'জনাবা', 'জনের',
    'জন্য', 'জানতাম', 'জানতে', 'জানা', 'জানানো', 'জানায়', 'জানিয়ে', 'জানিয়েছে', 'জানে', 'জায়গা',
    'জিজ্ঞাসা', 'জিজ্ঞেস', 'জিনিস', 'জে', 'জ্নজন', 'টা', 'টি', 'ঠিক', 'ঠিকআছে', 'ডগা', 'তখন', 'তত',
    'তত্কারণে', 'তত্প্রতি', 'তথা', 'তদনুসারে', 'তদ্ব্যতীত', 'তন্নতন্ন', 'তবু', 'তবে', 'তরুণ', 'তা',
    'তাঁকে', 'তাঁদের', 'তাঁর', 'তাঁরা', 'তাঁহারা', 'তাই', 'তাও', 'তাকে', 'তাতে', 'তাদের', 'তার', 'তারপর',
    'তারপরেও', 'তারা', 'তারিখ', 'তারৈ', 'তাহলে', 'তাহা', 'তাহাতে', 'তাহাদিগকে', 'তাহাদেরই', 'তাহার',
    'তিন', 'তিনি', 'তিনিও', 'তীক্ষ্ন', 'তুমি', 'তুলে', 'তেমন', 'তৈরীর', 'তো', 'তোমার', 'তোলে', 'থাকবে',
    'থাকবেন', 'থাকা', 'থাকায়', 'থাকায়', 'থাকে', 'থাকেন', 'থেকে', 'থেকেই', 'থেকেও', 'দরকারী', 'দলবদ্ধ',
    'দান', 'দিকে', 'দিতে', 'দিন', 'দিয়ে', 'দিয়েছে', 'দিয়েছেন', 'দিলেন', 'দিয়ে', 'দিয়েছে', 'দিয়েছেন',
    'দু', 'দুই', 'দুটি', 'দুটো', 'দূরে', 'দেওয়ার', 'দেওয়া', 'দেওয়ার', 'দেখতে', 'দেখা', 'দেখাচ্ছে',
    'দেখিয়েছেন', 'দেখে', 'দেখেন', 'দেন', 'দেয়', 'দেয়', 'দ্বারা', 'দ্বিগুণ', 'দ্বিতীয়', 'দ্য', 'ধরা',
    'ধরে', 'ধামার', 'নতুন', 'নব্বই', 'নয়', 'নাই', 'নাকি', 'নাগাদ', 'নানা', 'নাম', 'নিচে', 'নিছক',
    'নিজে', 'নিজেই', 'নিজেকে', 'নিজেদের', 'নিজেদেরকে', 'নিজের', 'নিতে', 'নিদিষ্ট', 'নিম্নাভিমুখে',
    'নিয়ে', 'নির্দিষ্ট', 'নির্বিশেষে', 'নিশ্চিত', 'নিয়ে', 'নেই', 'নেওয়ার', 'নেওয়া', 'নেয়ার', 'নয়',
    'পক্ষই', 'পক্ষে', 'পঞ্চম', 'পড়া', 'পণ্য', 'পথ', 'পয়েন্ট', 'পর', 'পরন্তু', 'পরবর্তী', 'পরিণত',
    'পরিবর্তে', 'পরে', 'পরেই', 'পরেও', 'পর্যন্ত', 'পর্যাপ্ত', 'পাঁচ', 'পাওয়া', 'পাচ', 'পায়', 'পারা',
    'পারি', 'পারিনি', 'পারে', 'পারেন', 'পালা', 'পাশ', 'পাশে', 'পিছনে', 'পিঠের', 'পুরোনো', 'পুরোপুরি',
    'পূর্বে', 'পৃষ্ঠা', 'পৃষ্ঠাগুলি', 'পেছনে', 'পেয়েছেন', 'পেয়ে', 'পেয়্র্', 'প্রকৃতপক্ষে', 'প্রণীত', 'প্রতি',
    'প্রথম', 'প্রদত্ত', 'প্রদর্শনী', 'প্রদর্শিত', 'প্রধানত', 'প্রবলভাবে', 'প্রভৃতি', 'প্রমাণীকরণ', 'প্রযন্ত',
    'প্রয়োজন', 'প্রয়োজনীয়', 'প্রসূত', 'প্রাক্তন', 'প্রাথমিক', 'প্রাথমিকভাবে', 'প্রান্ত', 'প্রাপ্ত',
    'প্রায়', 'প্রায়ই', 'প্রায়', 'ফলাফল','লাখ','জুন','টাকা','ফলে', 'ফিক্স', 'ফিরে', 'ফের', 'বক্তব্য', 'বছর', 'বড়', 'বদলে',
    'বন', 'বন্ধ', 'বরং', 'বরাবর', 'বর্ণন', 'বর্তমান', 'বলতে', 'বলল', 'বললেন', 'বলা', 'বলে', 'বলেছেন',
    'বলেন', 'বসে', 'বহু', 'কর','বা', 'বাঁক','বিএনপি', 'বাইরে', 'বাকি', 'বাড়ি', 'বাতিক', 'বাদ', 'বাদে', 'বার', 'বাহিরে',
    'বিনা', 'বিন্দু', 'বিভিন্ন', 'বিশেষ', 'বিশেষণ', 'বিশেষত', 'বিশেষভাবে', 'বিশ্ব', 'বিষয়টি', 'বুঝিয়ে',
    'বৃহত্তর', 'বের', 'বেশ', 'বেশি', 'বেশী', 'ব্যতীত', 'ব্যবহার', 'ব্যবহারসমূহ', 'ব্যবহৃত', 'ব্যাক',
    'ব্যাপকভাবে', 'ব্যাপারে', 'ভবিষ্যতে', 'ভান', 'ভাবে', 'ভাবেই', 'ভাল', 'ভিতরে', 'ভিন্ন', 'ভিন্নভাবে',
    'মত', 'মতো', 'মতোই', 'মধ্যভাগে', 'মধ্যে', 'মধ্যেই', 'মধ্যেও', 'মনে', 'মনে হয়', 'মস্ত', 'মহান',
    'মাত্র', 'মাধ্যম', 'মাধ্যমে', 'মান', 'মানানসই', 'মানুষ', 'মানে', 'মামলা', 'মিলিয়ন', 'মুখ', 'মূলত',
    'মোট', 'মোটেই', 'যখন', 'যখনই', 'যত', 'যতটা', 'যথা', 'যথাক্রমে', 'যথেষ্ট', 'যদি', 'যদিও', 'যন্ত্রাংশ',
    'যা', 'যাঁর', 'যাঁরা', 'যাই', 'যাওয়া', 'যাওয়ার', 'যাওয়া', 'যাওয়ার', 'যাকে', 'যাচ্ছে', 'যাতে', 'যাদের',
    'যান', 'যাবে', 'যায়', 'যার', 'যারা', 'যাহার', 'যাহোক', 'যিনি', 'যে', 'যেখানে', 'যেখানেই', 'যেটি',
    'যেতে', 'যেন', 'যেমন', 'যেহেতু', 'যোগ', 'রকম', 'রয়েছে', 'রাখা', 'রাখে', 'রাজী', 'রাজ্যের', 'রেখে',
    'রয়েছে', 'লক্ষ', 'লাইন', 'লাল', 'শত', 'শব্দ', 'শীঘ্র', 'শীঘ্রই', 'শুধু', 'শুরু', 'শুরুতে', 'শূন্য',
    'শেষ', 'সংক্রান্ত', 'সংক্ষিপ্ত', 'সংক্ষেপে', 'সংখ্যা', 'সংখ্যার', 'সংশ্লিষ্ট', 'সক্ষম', 'সঙ্গে',
    'সঙ্গেও', 'সত্য', 'সত্যিই', 'সদয়', 'সদস্য', 'সদস্যদের', 'সফলভাবে', 'সব', 'সবচেয়ে', 'সবাই', 'সবার',
    'সময়', 'সমস্ত', 'সমান', 'সম্পন্ন', 'সম্প্রতি', 'সম্ভব', 'সম্ভবত', 'সম্ভাব্য', 'সরাইয়া', 'সর্বত্র',
    'সর্বদা', 'সর্বস্বান্ত', 'সহ', 'সহিত', 'সাত', 'সাধারণ', 'সাধারণত', 'সাব', 'সাবেক', 'সামগ্রিক', 'সামনে',
    'সামান্য', 'সাম্প্রতিক', 'সুতরাং', 'সুত্র', 'সূচক', 'সে', 'সে হবে', 'সেই', 'সেকেন্ড', 'সেখান', 'সেখানে',
    'সেগুলো', 'সেটা', 'সেটাই', 'সেটাও', 'সেটি', 'সেরা', 'স্টপ', 'স্থাপিত', 'স্পষ্ট', 'স্পষ্টত', 'স্পষ্টতই',
    'স্ব', 'স্বয়ং', 'স্বাগত', 'স্বাভাবিকভাবে', 'স্বার্থ', 'স্বয়ং', 'হইতে', 'হইবে', 'হইয়া', 'হওয়া', 'হওয়ায়',
    'হওয়ার', 'হচ্ছে', 'হত', 'হতে', 'হতেই', 'হন', 'হবে', 'হবেন', 'হয়', 'হয়তো', 'হয়নি', 'হয়ে', 'হয়েই',
    'হয়েছিল', 'হয়েছে', 'হয়েছেন', 'হল', 'হলে', 'হলেই', 'হলেও', 'হলো', 'হাজার', 'হায়', 'হারানো',
    'হিসাবে', 'হৈলে', 'হোক', 'হয়', 'হয়তো', 'হয়নি', 'হয়ে', 'হয়েই', 'হয়েছিল', 'হয়েছে', 'হয়েছেন', 'অংশ'
])
