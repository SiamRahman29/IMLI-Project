import { useEffect, useState } from 'react';
import axios from 'axios';

function Home() {
  const [word, setWord] = useState('');
  const [date, setDate] = useState('');

  useEffect(() => {
    axios.get('http://localhost:8000/')
      .then(res => {
        if (res.data.word) {
          setWord(res.data.word);
          setDate(res.data.date);
        } else {
          setWord('আজকের শব্দ এখনো নির্ধারিত হয়নি');
        }
      })
      .catch(err => {
        setWord('সার্ভার ত্রুটি');
        console.error(err);
      });
  }, []);

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      height: '100vh', fontSize: '4rem', fontWeight: 'bold', textAlign: 'center'
    }}>
      {date && word ? `${date} - ${word}` : word}
    </div>
  );
}

export default Home;
