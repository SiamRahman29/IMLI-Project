import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiV2 } from '../api';
import { TrendingUp, Sparkles } from 'lucide-react';

function Home() {
  const [word, setWord] = useState('');
  const [date, setDate] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWordOfTheDay();
  }, []);

  const fetchWordOfTheDay = async () => {
    try {
      setLoading(true);
      const response = await apiV2.getWordOfTheDay();
      if (response.data.words) {
        setWord(response.data.words);
        setDate(response.data.date);
      }
    } catch (err) {
      setError('আজকের শব্দ এখনো নির্ধারণ করা হয়নি');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-center items-center bg-white">
        <svg className="animate-spin h-16 w-16 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
        <p className="mt-4 text-lg font-medium text-gray-700">লোড হচ্ছে...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12 bg-white min-h-[calc(100vh-4rem)] flex flex-col justify-center">
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-gray-900 mb-2">BARTA - IMLI</h1>
        <p className="text-xl text-gray-600 mb-2">বাংলা ট্রেন্ডিং শব্দ বিশ্লেষণ সিস্টেম</p>
      </div>

      {error ? (
        <div className="bg-blue-100 border border-blue-300 text-blue-800 px-4 py-3 rounded mb-8 text-center">
          {error}
        </div>
      ) : (
        <div className="bg-white shadow-lg rounded-lg mb-10 p-8 text-center">
          <h2 className="text-2xl font-bold mb-2">আজকের শব্দ</h2>
          {word ? (
            <>
              {date && (
                <div className="text-gray-500 mb-2">{new Date(date).toLocaleDateString('bn-BD')}</div>
              )}
              <div className="text-3xl font-extrabold text-blue-600 mt-2">{word}</div>
            </>
          ) : (
            <>
              <div className="text-gray-400 text-lg mb-4 font-semibold">আজকের জন্য কোনো শব্দ নির্ধারণ করা হয়নি।</div>
              <div className="text-gray-600 text-base">নির্বাচন করতে নিচের <span className='font-bold text-pink-600'>শব্দ উৎপাদন করুন</span> বাটনে ক্লিক করুন।</div>
            </>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
        <div className="bg-white shadow-md rounded-lg h-full flex flex-col items-center p-8 text-center">
          <TrendingUp className="w-14 h-14 text-blue-500 mb-3" />
          <h3 className="text-xl font-semibold mb-2">ট্রেন্ডিং বিশ্লেষণ</h3>
          <p className="text-gray-600 mb-4">সংবাদ ও সোশ্যাল মিডিয়া থেকে বর্তমান ট্রেন্ডিং শব্দ ও বাক্যাংশ দেখুন</p>
          <Link to="/trending" className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 rounded-lg transition mt-2 shadow focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2">বিশ্লেষণ দেখুন</Link>
        </div>
        <div className="bg-white shadow-md rounded-lg h-full flex flex-col items-center p-8 text-center">
          <Sparkles className="w-14 h-14 text-pink-500 mb-3" />
          <h3 className="text-xl font-semibold mb-2">শব্দ উৎপাদন</h3>
          <p className="text-gray-600 mb-4">নতুন ট্রেন্ডিং শব্দের প্রার্থী তৈরি করুন</p>
          <Link to="/generate" className="inline-block border border-pink-500 text-pink-600 hover:bg-pink-500 hover:text-white font-semibold px-6 py-2 rounded-lg transition mt-2 shadow focus:outline-none focus:ring-2 focus:ring-pink-400 focus:ring-offset-2">শব্দ তৈরি করুন</Link>
        </div>
      </div>

      <div className="text-center mt-16 py-6">
        {/* Optional: Add a footer or extra info here */}
      </div>
    </div>
  );
}

export default Home;
