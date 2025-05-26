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
          setWord('Today\'s word is not yet set');
        }
      })
      .catch(err => {
        setWord('Server error');
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
