import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="w-full bg-gray-50 border-t border-gray-200 py-6 mt-12 text-center text-sm text-gray-600 flex flex-col items-center gap-2">
      <div>
        Powered by <a href="https://barta-eight.vercel.app/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-semibold">BARTA</a> &copy; {currentYear}
      </div>
      <div>
        <a href="https://imli.portal.gov.bd/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-semibold">IMLI Official Website</a>
      </div>
    </footer>
  );
};

export default Footer;
