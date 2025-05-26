import { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function GenerateWords() {
  const [responseText, setResponseText] = useState('');
  const [selectedWord, setSelectedWord] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    axios.post('http://localhost:8000/generate_candidates')
      .then(res => {
        setResponseText(res.data.words);  // Adjust formatting if needed
      })
      .catch(err => {
        setResponseText('Something went wrong');
        console.error(err);
      });
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedWord) return;

    axios.post(`http://localhost:8000/set_word_of_the_day?new_word=${selectedWord}`)
      .then(() => navigate('/'))
      .catch(err => {
        alert('Failed to set');
        console.error(err);
      });
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <h2>Generated Words</h2>
      <pre>{responseText}</pre>
      <form onSubmit={handleSubmit} style={{ marginTop: '2rem' }}>
        <label>
          Choose word:
          <input
            type="text"
            value={selectedWord}
            onChange={e => setSelectedWord(e.target.value)}
            style={{ marginLeft: '1rem' }}
            required
          />
        </label>
        <button type="submit" style={{ marginLeft: '1rem' }}>Submit</button>
      </form>
    </div>
  );
}

export default GenerateWords;
